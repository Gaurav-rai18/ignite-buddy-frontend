"""
The trainee's LOCAL SQLite database (one file on this PC). Holds:
    chat_turns    relevant Q&A turns (questions answered by the knowledge base / model), so follow-ups have context
    audit_log     which device operations ran (what, when, outcome) - never the content of notes/clipboard/files
    assignments   pushed by the admin panel; the trainee tracks status (pending/done) locally
    timetable     the weekly timetable pushed by the admin panel
    kv            sync cursor
The server never reads this file. Chat turns older than CHAT_KEEP_DAYS and audit rows older than AUDIT_KEEP_DAYS are pruned.
"""
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from rapidfuzz import fuzz

SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_turns(id INTEGER PRIMARY KEY, ts REAL, question TEXT, answer TEXT);
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY, ts REAL, op TEXT, args TEXT, status TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS assignments(id TEXT PRIMARY KEY, title TEXT, description TEXT, due_ts REAL, status TEXT DEFAULT 'pending',
    updated_ts REAL);
CREATE TABLE IF NOT EXISTS timetable(id TEXT PRIMARY KEY, weekday INTEGER, start TEXT, end TEXT, title TEXT, location TEXT);
CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT);
"""
SENSITIVE_ARGS = {"text", "content", "query"}          # the audit log records THAT something happened, not the user's words


class LocalDB:
    def __init__(self, path):
        self.path = Path(path)
        self._lock, self._ready = threading.Lock(), False

    @contextmanager
    def conn(self):
        with self._lock:
            if not self._ready:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                boot = sqlite3.connect(self.path)
                boot.executescript(SCHEMA)
                boot.commit(); boot.close()
                self._ready = True
        con = sqlite3.connect(self.path, timeout=10)
        try:
            yield con
            con.commit()
        except BaseException:
            con.rollback(); raise
        finally:
            con.close()

    # ------------------------------ chat ------------------------------
    def add_chat(self, question: str, answer: str):
        with self.conn() as c:
            c.execute("INSERT INTO chat_turns(ts,question,answer) VALUES (?,?,?)", (time.time(), question[:2000], answer[:6000]))

    def chat_context(self, query: str = "", recent: int = 6, relevant: int = 3) -> list[dict]:
        """Last `recent` turns + up to `relevant` OLDER turns that look related to `query`, oldest first, as chat messages."""
        with self.conn() as c:
            rows = c.execute("SELECT id,question,answer FROM chat_turns ORDER BY id DESC LIMIT 200").fetchall()
        latest, older = rows[:recent], rows[recent:]
        picked = list(latest)
        q = (query or "").lower()
        if q and older:
            scored = sorted(((max(fuzz.token_set_ratio(q, r[1].lower()), fuzz.partial_ratio(q, (r[1] + " " + r[2]).lower())), r)
                             for r in older), key=lambda x: -x[0])
            picked += [r for sc, r in scored[:relevant] if sc >= 70]
        picked.sort(key=lambda r: r[0])
        out = []
        for _, qn, an in picked:
            out += [{"role": "user", "content": qn}, {"role": "assistant", "content": an}]
        return out

    def clear_chat(self) -> int:
        with self.conn() as c:
            n = c.execute("SELECT COUNT(*) FROM chat_turns").fetchone()[0]
            c.execute("DELETE FROM chat_turns")
        return n

    # ------------------------------ audit ------------------------------
    def audit(self, op: str, args: dict, status: str, detail: str = ""):
        safe = ", ".join(f"{k}=…" if k in SENSITIVE_ARGS else f"{k}={str(v)[:60]}" for k, v in (args or {}).items() if k != "choice")
        with self.conn() as c:
            c.execute("INSERT INTO audit_log(ts,op,args,status,detail) VALUES (?,?,?,?,?)", (time.time(), op, safe, status, detail[:200]))

    def recent_audit(self, n: int = 15):
        with self.conn() as c:
            return c.execute("SELECT ts,op,args,status FROM audit_log ORDER BY id DESC LIMIT ?", (n,)).fetchall()

    def clear_audit(self) -> int:
        with self.conn() as c:
            n = c.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
            c.execute("DELETE FROM audit_log")
        return n

    def prune(self, chat_days: int, audit_days: int):
        now = time.time()
        with self.conn() as c:
            c.execute("DELETE FROM chat_turns WHERE ts < ?", (now - chat_days * 86400,))
            c.execute("DELETE FROM audit_log WHERE ts < ?", (now - audit_days * 86400,))

    # ------------------------------ sync from the admin panel ------------------------------
    def cursor(self) -> int:
        with self.conn() as c:
            row = c.execute("SELECT value FROM kv WHERE key='sync_cursor'").fetchone()
        return int(row[0]) if row else 0

    def apply_sync(self, msg: dict) -> dict:
        """Apply a `sync` message. Local status of an assignment survives admin edits. Returns what changed (for a notification)."""
        changed = {"new": [], "updated": [], "removed": 0, "slots": 0}
        with self.conn() as c:
            for a in msg.get("assignments", []):
                aid = str(a["id"])
                if a.get("deleted"):
                    changed["removed"] += c.execute("DELETE FROM assignments WHERE id=?", (aid,)).rowcount
                    continue
                exists = c.execute("SELECT 1 FROM assignments WHERE id=?", (aid,)).fetchone()
                if exists:
                    c.execute("UPDATE assignments SET title=?,description=?,due_ts=?,updated_ts=? WHERE id=?",
                              (a["title"], a.get("description", ""), a.get("due_ts"), time.time(), aid))
                    changed["updated"].append(a["title"])
                else:
                    c.execute("INSERT INTO assignments(id,title,description,due_ts,status,updated_ts) VALUES (?,?,?,?,'pending',?)",
                              (aid, a["title"], a.get("description", ""), a.get("due_ts"), time.time()))
                    changed["new"].append(a["title"])
            for t in msg.get("timetable", []):
                tid = str(t["id"])
                if t.get("deleted"):
                    c.execute("DELETE FROM timetable WHERE id=?", (tid,))
                else:
                    def _pad(hm):
                        try:
                            h, m = str(hm).strip().split(":", 1)
                            return f"{int(h):02d}:{int(m):02d}"
                        except (TypeError, ValueError):
                            return str(hm)
                    c.execute("INSERT INTO timetable(id,weekday,start,end,title,location) VALUES (?,?,?,?,?,?) "
                              "ON CONFLICT(id) DO UPDATE SET weekday=excluded.weekday,start=excluded.start,end=excluded.end,"
                              "title=excluded.title,location=excluded.location",
                              (tid, int(t["weekday"]), _pad(t["start"]), _pad(t["end"]), t["title"], t.get("location", "")))
                changed["slots"] += 1
            if msg.get("cursor") is not None:
                c.execute("INSERT INTO kv(key,value) VALUES ('sync_cursor',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                          (str(int(msg["cursor"])),))
            meta = msg.get("trainee_meta")
            if isinstance(meta, dict) and meta:
                for k, v in meta.items():
                    if v is not None:
                        c.execute("INSERT INTO kv(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                                  (f"profile_{k}", str(v)))
        return changed

    # ------------------------------ profile / meta ------------------------------
    def get_meta(self, key: str, default: str = "") -> str:
        with self.conn() as c:
            row = c.execute("SELECT value FROM kv WHERE key=?", (f"profile_{key}",)).fetchone()
            if not row:
                row = c.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return str(row[0]) if row else default

    def set_meta(self, key: str, value: str):
        with self.conn() as c:
            c.execute("INSERT INTO kv(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                      (f"profile_{key}", str(value)))

    def profile(self) -> dict:
        with self.conn() as c:
            rows = c.execute("SELECT key, value FROM kv WHERE key LIKE 'profile_%'").fetchall()
        return {r[0].replace("profile_", ""): r[1] for r in rows}

    # ------------------------------ assignments / timetable ------------------------------
    def assignments(self):
        with self.conn() as c:
            return c.execute("SELECT id,title,description,due_ts,status FROM assignments ORDER BY (due_ts IS NULL), due_ts").fetchall()

    def set_assignment_status(self, aid: str, status: str):
        with self.conn() as c:
            c.execute("UPDATE assignments SET status=?, updated_ts=? WHERE id=?", (status, time.time(), aid))

    def slots(self, weekday: int | None = None):
        with self.conn() as c:
            if weekday is None:
                return c.execute("SELECT weekday,start,end,title,location FROM timetable ORDER BY weekday,start").fetchall()
            return c.execute("SELECT weekday,start,end,title,location FROM timetable WHERE weekday=? ORDER BY start", (weekday,)).fetchall()
