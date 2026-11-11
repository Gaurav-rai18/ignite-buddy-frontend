"""
Per-trainee storage on the SERVER (private to one trainee, isolated by construction):
    SQLite   : one file per trainee  DATA_DIR/users/<hash>/local.db           (development, tests)
    Postgres : one SCHEMA per trainee  u_<hash>   in DATABASE_URL            (production)
Services receive a Store and never build paths or schema names themselves. Vectors are NOT stored here (ChromaDB).
The trainee's own device keeps a separate LOCAL SQLite database (client/localdb.py).
"""
import hashlib
import os
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path

from server import config
from . import db
from . import migrate
from .schema import USER_SCHEMA


def _harden(folder: Path):
    """Best effort: only the service account may read the data folder."""
    try:
        if os.name == "nt":
            user = os.environ.get("USERNAME", "")
            subprocess.run(["icacls", str(folder), "/inheritance:r", "/grant:r", f"{user}:(OI)(CI)F",
                            "/grant:r", "SYSTEM:(OI)(CI)F"], capture_output=True, timeout=10)
        else:
            os.chmod(folder, 0o700)
    except Exception:
        pass


def user_key(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:24]       # no path traversal, no user names in schema/dir names


class Store:
    def __init__(self, user_id: str):
        if not user_id:
            raise ValueError("user_id required")
        self.user_id = user_id
        self.url = config.DATABASE_URL
        self.dialect = "postgres" if self.url else "sqlite"
        self.key = user_key(user_id)
        self.schema = f"u_{self.key}"
        self.dir = Path(config.USERS_DIR) / self.key
        self.path = self.dir / "local.db"
        self._ready = False
        self.upgrades: list[str] = []
        self._lock = threading.Lock()

    # ---------------- connections ----------------
    def _open(self) -> db.Conn:
        if self.dialect == "postgres":
            return db.open_postgres(self.url, self.schema)
        return db.open_sqlite(self.path)

    def _bootstrap(self):
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            if self.dialect == "postgres":
                import psycopg
                with psycopg.connect(self.url) as boot:
                    boot.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"')
                    boot.execute(f'SET search_path TO "{self.schema}"')
                    self.upgrades = migrate.bootstrap_postgres(boot, USER_SCHEMA)
            else:
                self.dir.mkdir(parents=True, exist_ok=True)
                _harden(config.USERS_DIR)
                _harden(self.dir)
                c = db.open_sqlite(self.path)
                try:
                    c.execute("PRAGMA journal_mode=WAL")       # request threads, scheduler and samples write concurrently
                except Exception:
                    pass                                       # another process is switching it right now: WAL is already set or will be
                self.upgrades = migrate.bootstrap_sqlite(c.raw, USER_SCHEMA)     # files from older releases get their new columns
                c.commit()
                c.close()
            if self.upgrades:
                import logging
                logging.getLogger("storage").warning("upgraded database of %s: added %s", self.key, ", ".join(self.upgrades))
            self._ready = True

    @contextmanager
    def conn(self):
        """with store.conn() as con: ...   commits on success, rolls back on error, always closes."""
        self._bootstrap()
        con = self._open()
        try:
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    # ---------------- settings ----------------
    def get_setting(self, key, default=None):
        with self.conn() as con:
            row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        with self.conn() as con:
            con.execute("INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, str(value)))

    # ---------------- chat memory ----------------
    def add_chat_turn(self, question: str, answer: str):
        """Persist a conversation turn (user query and assistant answer) in the trainee's private SQLite database."""
        import time
        now = time.time()
        with self.conn() as con:
            con.execute("INSERT INTO chat_history(ts, role, content) VALUES (?,?,?)", (now, "user", question))
            con.execute("INSERT INTO chat_history(ts, role, content) VALUES (?,?,?)", (now + 0.001, "assistant", answer))

    def get_chat_history(self, n_turns: int = 15) -> list[dict]:
        """Retrieve recent conversation turns from local SQLite storage in chronological order."""
        with self.conn() as con:
            rows = con.execute("SELECT role, content FROM chat_history ORDER BY id DESC LIMIT ?", (n_turns * 2,)).fetchall()
        rows.reverse()
        return [{"role": r[0], "content": r[1]} for r in rows]

    def clear_chat_history(self) -> int:
        """Erase all persisted chat memory records from local storage."""
        with self.conn() as con:
            n = con.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
            con.execute("DELETE FROM chat_history")
        return n

    # ---------------- erasure ----------------
    def purge_storage(self):
        """After rows are deleted: make the old bytes unrecoverable where the engine allows it."""
        if self.dialect == "sqlite":
            c = self._open()
            try:
                c.execute("VACUUM")                            # with secure_delete=ON the old content is overwritten
                c.execute("PRAGMA wal_checkpoint(TRUNCATE)")   # the write-ahead log also holds old copies
            finally:
                c.close()
        else:
            import psycopg
            with psycopg.connect(self.url, autocommit=True) as c:
                c.execute(f'SET search_path TO "{self.schema}"')
                for table in ("actions", "reminders", "timers", "activity_events", "summaries", "screen_history"):
                    c.execute(f'VACUUM FULL "{table}"')


_stores: dict[str, Store] = {}
_stores_lock = threading.Lock()


def get_store(user_id: str) -> Store:
    with _stores_lock:
        s = _stores.get(user_id)
        if s is None or s.dir.parent != Path(config.USERS_DIR) or s.url != config.DATABASE_URL:
            s = _stores[user_id] = Store(user_id)
        return s
