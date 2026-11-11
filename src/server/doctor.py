"""`trainee-doctor`: checks everything the server stores and prints WHAT is wrong and how to fix it.
It upgrades databases from older releases, verifies integrity, and opens the knowledge base."""
import sqlite3
import sys

from server import config


def main() -> int:
    bad = 0

    def line(ok, msg):
        nonlocal bad
        bad += 0 if ok else 1
        print(("  OK    " if ok else "  FAIL  ") + msg)

    print(f"SQLite {sqlite3.sqlite_version}, Python {sys.version.split()[0]}")
    print(f"Data folder: {config.DATA_DIR}")
    try:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        probe = config.DATA_DIR / ".doctor"
        probe.write_text("x"); probe.unlink()
        line(True, "data folder is writable")
    except OSError as e:
        line(False, f"data folder is not writable: {e}  -> set ASSISTANT_DATA to a folder you own")

    from server.data.central import Central
    try:
        c = Central()
        c._bootstrap()
        with c.conn() as con:
            n = con.execute("SELECT COUNT(*) FROM trainees").fetchone()[0]
        line(True, f"central database ({'PostgreSQL' if config.DATABASE_URL else 'SQLite'}) opens; {n} trainees")
    except Exception as e:
        line(False, f"central database: {type(e).__name__}: {e}")

    if config.DATABASE_URL:
        line(True, "per-trainee data is in PostgreSQL schemas u_*")
    else:
        from server.data.store import Store
        users = [p for p in config.USERS_DIR.glob("*/local.db")] if config.USERS_DIR.exists() else []
        for db in users:
            store = Store.__new__(Store)                                   # open by path, whatever user it belongs to
            try:
                from server.data import db as dbmod, migrate
                from server.data.schema import USER_SCHEMA
                con = dbmod.open_sqlite(db)
                changes = migrate.bootstrap_sqlite(con.raw, USER_SCHEMA)
                con.commit()
                verdict = con.execute("PRAGMA integrity_check").fetchone()[0]
                con.close()
                line(verdict == "ok", f"{db.parent.name}: integrity {verdict}" + (f"; UPGRADED, added {', '.join(changes)}" if changes else ""))
            except Exception as e:
                line(False, f"{db}: {type(e).__name__}: {e}  -> move this folder away to start fresh")
        if not users:
            line(True, "no trainee databases yet")

    try:
        from server.knowledge.store import get_kb
        stats = get_kb().stats()
        line(True, "knowledge base (ChromaDB) opens: " + ", ".join(f"{k}={v['chunks']} chunks" for k, v in stats.items()))
    except Exception as e:
        line(False, f"knowledge base at {config.KB_PATH}: {type(e).__name__}: {e}  "
                    "-> if it says 'locked', only ONE server process may use KB_PATH; if 'no such column/table', "
                    "the folder came from another ChromaDB version: move it away and re-run `trainee-kb ingest`")
    print("\nAll good." if not bad else f"\n{bad} problem(s) found.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
