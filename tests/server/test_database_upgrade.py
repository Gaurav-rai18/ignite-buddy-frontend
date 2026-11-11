"""Databases created by EARLIER releases must keep working: this was an `OperationalError: no such column: native` every second."""
import os
import sqlite3
import threading
import time

import pytest
from server import config
from server.features import personal
from server.jobs import runner
from server.data import migrate
from server.data.central import Central
from server.data.schema import CENTRAL_SCHEMA, USER_SCHEMA
from server.data.store import Store

LEGACY = """
CREATE TABLE files(id INTEGER PRIMARY KEY, path TEXT);
CREATE TABLE chunks(id INTEGER PRIMARY KEY, path TEXT, page INTEGER, file_hash TEXT, text TEXT, emb BLOB);
CREATE TABLE actions(id INTEGER PRIMARY KEY, ts TEXT DEFAULT CURRENT_TIMESTAMP, tool TEXT, args TEXT, status TEXT, detail TEXT);
CREATE TABLE notes(id INTEGER PRIMARY KEY, ts REAL, text TEXT, emb BLOB);
CREATE TABLE reminders(id INTEGER PRIMARY KEY, text TEXT, due REAL, repeat TEXT DEFAULT '', status TEXT DEFAULT 'pending');
CREATE TABLE timers(id INTEGER PRIMARY KEY, label TEXT, end_ts REAL, status TEXT DEFAULT 'pending');
CREATE TABLE activity_events(id INTEGER PRIMARY KEY, start_ts REAL, end_ts REAL, app TEXT, title TEXT, idle INTEGER);
CREATE TABLE summaries(id INTEGER PRIMARY KEY, day TEXT, kind TEXT, start_ts REAL, end_ts REAL, text TEXT, emb BLOB, created REAL);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE screen_history(id INTEGER PRIMARY KEY, ts REAL, app TEXT, title TEXT, question TEXT, answer TEXT);
INSERT INTO timers(label,end_ts) VALUES ('kept', 1);
INSERT INTO settings(key,value) VALUES ('app_blocklist','["foo"]');
"""

pytestmark = pytest.mark.skipif(bool(os.getenv("DATABASE_URL")), reason="SQLite file-upgrade scenarios")


def legacy_store(uid):
    s = Store(uid)
    s.dir.mkdir(parents=True, exist_ok=True)
    raw = sqlite3.connect(s.path); raw.executescript(LEGACY); raw.commit(); raw.close()
    return s


def test_old_database_is_upgraded_automatically_and_keeps_its_data():
    s = legacy_store("legacy-user-1")
    sent = []
    runner.tick(s, sent.append, now=time.time() + 5)               # used to raise "no such column: native"
    assert [m["text"] for m in sent] == ["Timer finished (missed): kept"]
    personal.add_timer(s, 60, "new")
    personal.mark_native(s, "timers", 2)
    assert personal.is_native(s, "timers", 2)
    assert s.get_setting("app_blocklist") == '["foo"]'             # existing data untouched
    assert "reminders.native" in s.upgrades and "timers.native" in s.upgrades


def test_upgrade_is_idempotent_and_adds_nothing_when_current(tmp_path):
    raw = sqlite3.connect(tmp_path / "x.db")
    assert migrate.bootstrap_sqlite(raw, USER_SCHEMA) == []        # fresh database: nothing to upgrade
    assert migrate.bootstrap_sqlite(raw, USER_SCHEMA) == []
    raw.execute("ALTER TABLE reminders DROP COLUMN native")        # simulate an old file
    assert migrate.bootstrap_sqlite(raw, USER_SCHEMA) == ["reminders.native"]


def test_central_database_upgrade(tmp_path):
    raw = sqlite3.connect(tmp_path / "c.db")
    raw.executescript("CREATE TABLE trainees(user_id TEXT PRIMARY KEY, name TEXT);")       # an older shape without batch/created
    raw.commit(); raw.close()
    c = Central(url="", path=tmp_path / "c.db")
    assert c.trainee("a", "A")["batch"] == "default"


def test_a_busy_database_is_waited_for_not_reported_as_an_error():
    s = Store("busy-user")
    with s.conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES ('k','v') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
    blocker = sqlite3.connect(s.path, timeout=5, check_same_thread=False)
    blocker.execute("BEGIN IMMEDIATE")                             # another process holds the write lock for ~1 s
    threading.Timer(1.0, blocker.rollback).start()
    t0 = time.time()
    s.set_setting("k", "v2")                                       # must wait and succeed, not raise "database is locked"
    assert s.get_setting("k") == "v2" and 0.5 < time.time() - t0 < 8


def test_doctor_reports_and_repairs(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path); monkeypatch.setattr(config, "USERS_DIR", tmp_path / "users")
    monkeypatch.setattr(config, "KB_PATH", tmp_path / "kb")
    from server.knowledge import store as kbstore
    kbstore.set_kb(None)
    s = Store("doc-user"); s.dir.mkdir(parents=True)
    raw = sqlite3.connect(s.path); raw.executescript(LEGACY); raw.commit(); raw.close()
    from server import doctor
    assert doctor.main() == 0
    out = capsys.readouterr().out
    assert "UPGRADED, added reminders.native, timers.native" in out and "integrity ok" in out and "All good" in out
    kbstore.set_kb(None)


