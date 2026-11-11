import os
import uuid
import pytest

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="needs PostgreSQL (DATABASE_URL)")


def test_postgres_schema_from_an_old_release_is_upgraded():
    import psycopg
    from server import config
    from server.features import personal
    from server.data.store import Store
    uid = "pg-legacy-" + uuid.uuid4().hex[:6]
    s = Store(uid)
    with psycopg.connect(config.DATABASE_URL, autocommit=True) as c:
        c.execute(f'CREATE SCHEMA "{s.schema}"')
        c.execute(f'SET search_path TO "{s.schema}"')
        c.execute("CREATE TABLE timers(id BIGSERIAL PRIMARY KEY, label TEXT, end_ts DOUBLE PRECISION, status TEXT DEFAULT 'pending')")
        c.execute("INSERT INTO timers(label,end_ts) VALUES ('kept', 1)")
    tid = personal.add_timer(s, 60, "x")                           # first use upgrades the table
    personal.mark_native(s, "timers", tid)
    assert personal.is_native(s, "timers", tid) and "timers.native" in s.upgrades
    assert any(r[1] == "kept" for r in personal.pending_timers(s))  # old row survived
