"""
Schema upgrades for databases created by an EARLIER release. `CREATE TABLE IF NOT EXISTS` never changes an existing table,
so a file from an older version lacks newer columns and every query that mentions them fails with
"OperationalError: no such column: ...". This module compares the real database with the current schema (SQLite in-memory is
the reference) and adds whatever is missing, for SQLite and PostgreSQL alike. It only ADDS columns/tables; it never drops data.
"""
import re
import sqlite3

from .schema import pg_ddl


def _split(sql: str) -> tuple[list[str], list[str]]:
    stmts = [s.strip() for s in sql.split(";") if s.strip()]
    return [s for s in stmts if not s.upper().startswith("CREATE INDEX")], [s for s in stmts if s.upper().startswith("CREATE INDEX")]


def _reference(schema_sql: str) -> dict[str, list[tuple]]:
    ref = sqlite3.connect(":memory:")
    ref.executescript(schema_sql)
    out = {}
    for (table,) in ref.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        out[table] = [(r[1], r[2] or "TEXT", r[4], r[5]) for r in ref.execute(f"PRAGMA table_info({table})")]   # name,type,default,pk
    ref.close()
    return out


def _add_column_sql(table: str, name: str, typ: str, default, postgres: bool) -> str:
    if postgres:
        typ = pg_ddl(typ)
    ddl = f'ALTER TABLE {table} ADD COLUMN {"IF NOT EXISTS " if postgres else ""}{name} {typ}'
    return ddl + (f" DEFAULT {default}" if default is not None else "")


def bootstrap_sqlite(raw: sqlite3.Connection, schema_sql: str) -> list[str]:
    """Create missing tables, add missing columns, then create indexes. -> list of upgrade steps that were needed."""
    tables, indexes = _split(schema_sql)
    for stmt in tables:
        raw.execute(stmt)
    changes = []
    for table, cols in _reference(schema_sql).items():
        existing = {r[1] for r in raw.execute(f"PRAGMA table_info({table})")}
        for name, typ, default, pk in cols:
            if name not in existing and not pk:
                raw.execute(_add_column_sql(table, name, typ, default, False))
                changes.append(f"{table}.{name}")
    for stmt in indexes:
        raw.execute(stmt)
    return changes


def bootstrap_postgres(raw, schema_sql: str) -> list[str]:
    """Same for PostgreSQL (the connection's search_path already points at the right schema)."""
    tables, indexes = _split(pg_ddl(schema_sql))
    for stmt in tables:
        raw.execute(stmt)
    changes = []
    for table, cols in _reference(schema_sql).items():
        have = {r[0] for r in raw.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = %s", (table,)).fetchall()}
        for name, typ, default, pk in cols:
            if name not in have and not pk:
                raw.execute(_add_column_sql(table, name, typ, default, True))
                changes.append(f"{table}.{name}")
    for stmt in indexes:
        raw.execute(stmt)
    return changes
