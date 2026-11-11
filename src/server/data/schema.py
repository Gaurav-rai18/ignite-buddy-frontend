"""Relational schema, written once in portable SQL and adapted for PostgreSQL by pg_ddl().
NOTE: no embeddings here: vectors live in ChromaDB (kb/personal.py, features/activity/summarize.py)."""
import re

USER_SCHEMA = """
CREATE TABLE IF NOT EXISTS actions(
    id INTEGER PRIMARY KEY, ts REAL, tool TEXT, args TEXT, status TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS reminders(
    id INTEGER PRIMARY KEY, text TEXT, due REAL, repeat TEXT DEFAULT '', status TEXT DEFAULT 'pending', native INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS timers(
    id INTEGER PRIMARY KEY, label TEXT, end_ts REAL, status TEXT DEFAULT 'pending', native INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS activity_events(
    id INTEGER PRIMARY KEY, start_ts REAL, end_ts REAL, app TEXT, title TEXT, idle INTEGER);
CREATE INDEX IF NOT EXISTS idx_activity_start ON activity_events(start_ts);
CREATE TABLE IF NOT EXISTS summaries(
    id INTEGER PRIMARY KEY, day TEXT, kind TEXT, start_ts REAL, end_ts REAL, text TEXT, created REAL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS screen_history(
    id INTEGER PRIMARY KEY, ts REAL, app TEXT, title TEXT, question TEXT, answer TEXT);
CREATE TABLE IF NOT EXISTS chat_history(
    id INTEGER PRIMARY KEY, ts REAL, role TEXT, content TEXT);
CREATE INDEX IF NOT EXISTS idx_chat_history_ts ON chat_history(ts);
"""

# shared (cross-trainee) tables: what the admin panel publishes, and who is in which batch
CENTRAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS trainees(
    user_id TEXT PRIMARY KEY, name TEXT, batch TEXT DEFAULT 'default',
    password_hash TEXT DEFAULT '', created REAL);
CREATE TABLE IF NOT EXISTS assignments(
    id TEXT PRIMARY KEY, batch TEXT, title TEXT, description TEXT, due_ts REAL, deleted INTEGER DEFAULT 0, rev BIGINT);
CREATE TABLE IF NOT EXISTS timetable_slots(
    id TEXT PRIMARY KEY, batch TEXT, weekday INTEGER, start_time TEXT, end_time TEXT, title TEXT, location TEXT,
    deleted INTEGER DEFAULT 0, rev BIGINT);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v BIGINT);
CREATE INDEX IF NOT EXISTS idx_assignments_rev ON assignments(rev);
CREATE INDEX IF NOT EXISTS idx_slots_rev ON timetable_slots(rev);
"""


def pg_ddl(sql: str) -> str:
    sql = sql.replace("INTEGER PRIMARY KEY", "BIGSERIAL PRIMARY KEY")
    return re.sub(r"\bREAL\b", "DOUBLE PRECISION", sql)
