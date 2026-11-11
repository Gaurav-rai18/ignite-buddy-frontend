"""One tiny connection wrapper so the rest of the server writes ONE dialect of SQL (qmark `?` placeholders) and runs on
SQLite (dev/tests) or PostgreSQL (production)."""
import sqlite3
import time


class Conn:
    def __init__(self, raw, dialect: str):
        self.raw, self.dialect = raw, dialect

    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.dialect == "postgres" else sql

    def execute(self, sql: str, params=()):
        sql = self._sql(sql)
        for attempt in range(3):
            try:
                return self.raw.execute(sql, tuple(params))
            except sqlite3.OperationalError as e:                      # another writer holds the file: wait a little, then retry
                if self.dialect != "sqlite" or "locked" not in str(e) and "busy" not in str(e) or attempt == 2:
                    raise
                time.sleep(0.15 * (attempt + 1))

    def executemany(self, sql: str, rows):
        cur = self.raw.cursor()
        cur.executemany(self._sql(sql), [tuple(r) for r in rows])
        return cur

    def insert(self, sql: str, params=()) -> int:
        """INSERT into a table with an integer `id` primary key -> the new id (portable lastrowid)."""
        if self.dialect == "postgres":
            return self.execute(sql + " RETURNING id", params).fetchone()[0]
        return self.execute(sql, params).lastrowid

    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()


def open_sqlite(path) -> Conn:
    raw = sqlite3.connect(path, timeout=15)
    raw.execute("PRAGMA busy_timeout=15000")
    raw.execute("PRAGMA secure_delete=ON")                       # deleted rows are overwritten, not just unlinked
    return Conn(raw, "sqlite")


def open_postgres(url: str, schema: str | None = None) -> Conn:
    import psycopg
    raw = psycopg.connect(url)
    if schema:
        raw.execute(f'SET search_path TO "{schema}", public')
    return Conn(raw, "postgres")
