"""Reminders and timers: plain functions over ONE user's store. (Notes and tasks live on the trainee's PC.)"""
import time
from datetime import datetime


def fmt_dt(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%a %d %b, %I:%M %p")


# ---------- reminders ----------
def add_reminder(store, text: str, due: datetime, repeat: str = "") -> int:
    with store.conn() as con:
        return con.insert("INSERT INTO reminders(text,due,repeat,status) VALUES (?,?,?,'pending')",
                          (text, due.timestamp(), repeat))


def pending_reminders(store):
    with store.conn() as con:
        return con.execute("SELECT id,text,due,repeat FROM reminders WHERE status='pending' ORDER BY due").fetchall()


def cancel_reminder(store, rid: int):
    with store.conn() as con:
        con.execute("UPDATE reminders SET status='cancelled' WHERE id=?", (rid,))


# ---------- timers ----------
def add_timer(store, seconds: int, label: str = "") -> int:
    with store.conn() as con:
        return con.insert("INSERT INTO timers(label,end_ts,status) VALUES (?,?,'pending')",
                          (label, time.time() + seconds))


def pending_timers(store):
    with store.conn() as con:
        return con.execute("SELECT id,label,end_ts FROM timers WHERE status='pending' ORDER BY end_ts").fetchall()


def cancel_timer(store, tid: int):
    with store.conn() as con:
        con.execute("UPDATE timers SET status='cancelled' WHERE id=?", (tid,))


def mark_native(store, table: str, row_id: int):
    assert table in ("reminders", "timers")
    with store.conn() as con:
        con.execute(f"UPDATE {table} SET native=1 WHERE id=?", (row_id,))


def is_native(store, table: str, row_id: int) -> bool:
    assert table in ("reminders", "timers")
    with store.conn() as con:
        row = con.execute(f"SELECT native FROM {table} WHERE id=?", (row_id,)).fetchone()
    return bool(row and row[0])
