"""
Shared (cross-trainee) data: who is in which batch, and what the ADMIN PANEL publishes (assignments, weekly timetable).
Every change gets a monotonically increasing `rev`; a trainee's PC remembers the highest rev it applied (sync cursor) and
the server sends only newer rows. Deleted rows stay as tombstones so offline PCs learn about the deletion.
Batch "*" = visible to every batch.
"""
import threading
import time
import uuid

from server import config
from . import db
from . import migrate
from .schema import CENTRAL_SCHEMA

ALL = "*"


class Central:
    def __init__(self, url: str | None = None, path=None):
        self.url = config.DATABASE_URL if url is None else url
        self.path = path or (config.DATA_DIR / "central.db")
        self._ready, self._lock = False, threading.Lock()

    def _open(self) -> db.Conn:
        return db.open_postgres(self.url) if self.url else db.open_sqlite(self.path)

    def conn(self):
        from contextlib import contextmanager

        @contextmanager
        def cm():
            self._bootstrap()
            c = self._open()
            try:
                yield c
                c.commit()
            except BaseException:
                c.rollback()
                raise
            finally:
                c.close()
        return cm()

    def _bootstrap(self):
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            if not self.url:
                from pathlib import Path
                Path(self.path).parent.mkdir(parents=True, exist_ok=True)      # first run on a fresh server
            c = self._open()
            (migrate.bootstrap_postgres if self.url else migrate.bootstrap_sqlite)(c.raw, CENTRAL_SCHEMA)
            c.execute("INSERT INTO meta(k,v) VALUES ('rev',0) ON CONFLICT(k) DO NOTHING")
            c.commit(); c.close()
            self._ready = True

    @staticmethod
    def _bump(c) -> int:
        c.execute("UPDATE meta SET v=v+1 WHERE k='rev'")
        return c.execute("SELECT v FROM meta WHERE k='rev'").fetchone()[0]

    # ---------------- trainees ----------------
    def trainee(self, user_id: str, name: str = "") -> dict:
        """The trainee's row; created on first sight (batch 'default') so every login is known to the admin panel."""
        with self.conn() as c:
            c.execute("INSERT INTO trainees(user_id,name,batch,password_hash,created) VALUES (?,?,'default','',?) ON CONFLICT(user_id) DO NOTHING",
                      (user_id, name, time.time()))
            row = c.execute("SELECT user_id,name,batch,password_hash FROM trainees WHERE user_id=?", (user_id,)).fetchone()
        return {"user_id": row[0], "name": row[1], "batch": row[2], "password_hash": (row[3] if len(row) > 3 else "")}

    def set_batch(self, user_id: str, batch: str):
        with self.conn() as c:
            c.execute("UPDATE trainees SET batch=? WHERE user_id=?", (batch, user_id))

    def trainees(self) -> list[dict]:
        with self.conn() as c:
            return [{"user_id": r[0], "name": r[1], "batch": r[2], "has_password": bool(r[3])}
                    for r in c.execute("SELECT user_id,name,batch,password_hash FROM trainees ORDER BY user_id").fetchall()]

    def create_trainee(self, user_id: str, name: str, batch: str = "default", password: str = "") -> dict:
        """Admin creates a trainee profile (with optional password for desktop JWT login)."""
        from server.auth import hash_password
        ph = hash_password(password) if password else ""
        with self.conn() as c:
            c.execute(
                "INSERT INTO trainees(user_id,name,batch,password_hash,created) VALUES (?,?,?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET name=excluded.name, batch=excluded.batch, "
                "password_hash=CASE WHEN excluded.password_hash!='' THEN excluded.password_hash ELSE trainees.password_hash END",
                (user_id, name or user_id, batch or "default", ph, __import__("time").time()),
            )
            row = c.execute("SELECT user_id,name,batch,password_hash FROM trainees WHERE user_id=?", (user_id,)).fetchone()
        return {"user_id": row[0], "name": row[1], "batch": row[2], "has_password": bool(row[3])}

    def set_password(self, user_id: str, password: str) -> bool:
        from server.auth import hash_password
        with self.conn() as c:
            cur = c.execute("UPDATE trainees SET password_hash=? WHERE user_id=?", (hash_password(password), user_id))
            return cur.rowcount > 0

    def authenticate(self, user_id: str, password: str) -> dict | None:
        """Return trainee row dict if password matches, else None."""
        from server.auth import verify_password
        with self.conn() as c:
            row = c.execute("SELECT user_id,name,batch,password_hash FROM trainees WHERE user_id=?", (user_id,)).fetchone()
        if not row or not row[3]:
            return None
        if not verify_password(password, row[3]):
            return None
        return {"user_id": row[0], "name": row[1], "batch": row[2]}


    # ---------------- assignments ----------------
    def upsert_assignment(self, batch: str, title: str, description: str = "", due_ts: float | None = None, aid: str | None = None) -> str:
        aid = aid or uuid.uuid4().hex[:12]
        with self.conn() as c:
            rev = self._bump(c)
            c.execute("INSERT INTO assignments(id,batch,title,description,due_ts,deleted,rev) VALUES (?,?,?,?,?,0,?) "
                      "ON CONFLICT(id) DO UPDATE SET batch=excluded.batch,title=excluded.title,description=excluded.description,"
                      "due_ts=excluded.due_ts,deleted=0,rev=excluded.rev", (aid, batch, title, description, due_ts, rev))
        return aid

    def delete_assignment(self, aid: str) -> str | None:
        with self.conn() as c:
            row = c.execute("SELECT batch FROM assignments WHERE id=?", (aid,)).fetchone()
            if row:
                c.execute("UPDATE assignments SET deleted=1, rev=? WHERE id=?", (self._bump(c), aid))
        return row[0] if row else None

    def assignment_batch(self, aid: str) -> str | None:
        with self.conn() as c:
            row = c.execute("SELECT batch FROM assignments WHERE id=?", (aid,)).fetchone()
        return row[0] if row else None

    def assignments(self, batch: str | None = None) -> list[dict]:
        sql, p = "SELECT id,batch,title,description,due_ts FROM assignments WHERE deleted=0", []
        if batch:
            sql, p = sql + " AND (batch=? OR batch=?)", [batch, ALL]
        with self.conn() as c:
            return [dict(zip(("id", "batch", "title", "description", "due_ts"), r))
                    for r in c.execute(sql + " ORDER BY due_ts", p).fetchall()]

    # ---------------- timetable ----------------
    def upsert_slot(self, batch: str, weekday: int, start: str, end: str, title: str, location: str = "", sid: str | None = None) -> str:
        if not 0 <= int(weekday) <= 6:
            raise ValueError("weekday must be 0 (Monday) .. 6 (Sunday)")
        def _pad(hm: str) -> str:
            try:
                h, m = str(hm).strip().split(":", 1)
                return f"{int(h):02d}:{int(m):02d}"
            except (TypeError, ValueError):
                return str(hm)
        start, end = _pad(start), _pad(end)
        sid = sid or uuid.uuid4().hex[:12]
        with self.conn() as c:
            rev = self._bump(c)
            c.execute("INSERT INTO timetable_slots(id,batch,weekday,start_time,end_time,title,location,deleted,rev) VALUES (?,?,?,?,?,?,?,0,?) "
                      "ON CONFLICT(id) DO UPDATE SET batch=excluded.batch,weekday=excluded.weekday,start_time=excluded.start_time,"
                      "end_time=excluded.end_time,title=excluded.title,location=excluded.location,deleted=0,rev=excluded.rev",
                      (sid, batch, int(weekday), start, end, title, location, rev))
        return sid

    def delete_slot(self, sid: str) -> str | None:
        """Mark a timetable slot as deleted, increment the sync revision, and return its batch name."""
        with self.conn() as c:
            row = c.execute("SELECT batch FROM timetable_slots WHERE id=?", (sid,)).fetchone()
            if row:
                c.execute("UPDATE timetable_slots SET deleted=1, rev=? WHERE id=?", (self._bump(c), sid))
        return row[0] if row else None

    def delete_batch_slots(self, batch: str) -> int:
        """Mark all timetable slots for a batch or sub-batch as deleted."""
        with self.conn() as c:
            count = c.execute("SELECT count(*) FROM timetable_slots WHERE batch=? AND deleted=0", (batch,)).fetchone()[0]
            if count > 0:
                c.execute("UPDATE timetable_slots SET deleted=1, rev=? WHERE batch=? AND deleted=0", (self._bump(c), batch))
        return count

    def delete_all_slots(self) -> int:
        """Mark all timetable slots as deleted and bump revision."""
        with self.conn() as c:
            count = c.execute("SELECT count(*) FROM timetable_slots WHERE deleted=0").fetchone()[0]
            if count > 0:
                c.execute("UPDATE timetable_slots SET deleted=1, rev=? WHERE deleted=0", (self._bump(c),))
        return count

    def slot_batch(self, sid: str) -> str | None:
        """Look up the batch associated with a timetable slot ID, or None if not found."""
        with self.conn() as c:
            row = c.execute("SELECT batch FROM timetable_slots WHERE id=?", (sid,)).fetchone()
        return row[0] if row else None

    def slots(self, batch=None) -> list[dict]:
        sql, p = "SELECT id,batch,weekday,start_time,end_time,title,location FROM timetable_slots WHERE deleted=0", []
        if batch:
            cands = _normalize_batch_candidates(batch)
            ph = ",".join("?" for _ in cands)
            sql = sql + f" AND batch IN ({ph})"
            p.extend(cands)
        with self.conn() as c:
            return [dict(zip(("id", "batch", "weekday", "start", "end", "title", "location"), r))
                    for r in c.execute(sql + " ORDER BY weekday,start_time", p).fetchall()]

    # ---------------- sync ----------------
    def changes_since(self, batch, cursor: int) -> dict:
        """Everything a PC matching `batch` (or batch aliases) has not seen yet (including deletions)."""
        cands = _normalize_batch_candidates(batch)
        ph = ",".join("?" for _ in cands)
        with self.conn() as c:
            a = c.execute(f"SELECT id,title,description,due_ts,deleted,rev FROM assignments WHERE rev>? AND batch IN ({ph}) ORDER BY rev",
                          [cursor, *cands]).fetchall()
            t = c.execute(f"SELECT id,weekday,start_time,end_time,title,location,deleted,rev FROM timetable_slots "
                          f"WHERE rev>? AND batch IN ({ph}) ORDER BY rev", [cursor, *cands]).fetchall()
            top = c.execute("SELECT v FROM meta WHERE k='rev'").fetchone()[0]
        return {
            "cursor": max([cursor, *[r[5] for r in a], *[r[7] for r in t]] + [0]) if (a or t) else cursor,
            "head": top,
            "assignments": [{"id": r[0], "title": r[1], "description": r[2], "due_ts": r[3], "deleted": bool(r[4])} for r in a],
            "timetable": [{"id": r[0], "weekday": r[1], "start": r[2], "end": r[3], "title": r[4], "location": r[5], "deleted": bool(r[6])} for r in t],
        }


def _normalize_batch_candidates(batch) -> list[str]:
    cands = {ALL}
    if not batch:
        return list(cands)
    raw_list = batch if isinstance(batch, (list, tuple, set)) else [batch]
    for item in raw_list:
        s = str(item or "").strip()
        if not s:
            continue
        cands.add(s)
        if "-" in s:
            for part in s.split("-"):
                if part.strip():
                    cands.add(part.strip())
    return list(cands)


_central: Central | None = None
_cl = threading.Lock()


def get_central() -> Central:
    global _central
    with _cl:
        if _central is None or _central.url != config.DATABASE_URL:
            _central = Central()
        return _central
