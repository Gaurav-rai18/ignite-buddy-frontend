"""
Background scheduler. Works ONLY for users who are connected (their devices receive the notification); anything that
came due while offline fires once, marked "(missed)", when they next connect. One pass per second; every call is
scoped to one user's store, so a slow user never delays others for long.
"""
import logging
import threading
import time
from datetime import date, datetime, timedelta

from server import config
from server.domain import policy
from server.features import personal
from server.features.activity import summarize
from server.features.activity.recorder import recorder_for
from server.data.store import get_store
from server.realtime import notifier, presence

log = logging.getLogger("scheduler")
MISSED_AFTER = 120            # seconds late before an item is labelled "(missed)"
ASSIGNMENT_REMINDER_EVERY = 60  # seconds between deadline-reminder scans
_state: dict[str, dict] = {}
_last_error: dict[str, float] = {}
_last_assignment_scan = 0.0


def tick(store, send, now: float | None = None):
    """Fire everything due for ONE user. `send(msg_dict)` delivers to that user's devices."""
    now = now or time.time()
    if policy.is_blocked(store.user_id):
        return
    with store.conn() as con:
        for rid, text, due, repeat, native in con.execute(
                "SELECT id,text,due,repeat,native FROM reminders WHERE status='pending' AND due<=?", (now,)).fetchall():
            late = " (missed)" if now - due > MISSED_AFTER else ""
            if not native:                          # natively scheduled ones are shown by Windows itself
                send({"type": "notification", "kind": "reminder", "text": f"Reminder{late}: {text}"})
            if repeat:
                step = timedelta(days=1 if repeat == "daily" else 7).total_seconds()
                nxt = due + step
                while nxt <= now:
                    nxt += step
                con.execute("UPDATE reminders SET due=? WHERE id=?", (nxt, rid))
            else:
                con.execute("UPDATE reminders SET status='done' WHERE id=?", (rid,))
        for tid, label, end, native in con.execute(
                "SELECT id,label,end_ts,native FROM timers WHERE status='pending' AND end_ts<=?", (now,)).fetchall():
            late = " (missed)" if now - end > MISSED_AFTER else ""
            if not native:
                send({"type": "notification", "kind": "timer", "text": f"Timer finished{late}: {label or 'your timer'}"})
            con.execute("UPDATE timers SET status='done' WHERE id=?", (tid,))


def maybe_daily_summary(store, send, now: datetime | None = None):
    """Once per day after DAILY_SUMMARY_AT, generate today's summary in the background (cached for later)."""
    now = now or datetime.now()
    st = _state.setdefault(store.user_id, {})
    h, m = config.DAILY_SUMMARY_AT
    if now < now.replace(hour=h, minute=m, second=0, microsecond=0) or st.get("summary_day") == now.date() or st.get("busy"):
        return False
    day = now.date()
    if not summarize.has_activity(store, day):
        st["summary_day"] = day
        return False
    st["busy"] = True

    def work():
        try:
            summarize.generate_day_summary_text(store, day)
            send({"type": "notification", "kind": "summary", "text": "Your daily summary is ready. Say 'summarize my day'."})
            st["summary_day"] = day
        except Exception:
            log.exception("daily summary failed")
        finally:
            st["busy"] = False
    threading.Thread(target=work, daemon=True).start()
    return True


def tick_all(now: float | None = None):
    for uid in presence.user_ids():
        store = get_store(uid)
        send = lambda msg, uid=uid: notifier.push(uid, msg)       # noqa: E731
        try:
            tick(store, send, now)
        except Exception as e:
            key = f"{uid}:{type(e).__name__}:{e}"
            if time.time() - _last_error.get(key, 0) > 300:            # the same error is reported once per 5 minutes
                _last_error[key] = time.time()
                log.exception("scheduler failed for one user (run `trainee-doctor`): %s", e)


def tick_assignments(now: float | None = None) -> int:
    """Scan published assignments and dispatch the 24h / 1h deadline reminders.

    Persisted through the shared notification service, so this is safe to run on
    every tick: reminder flags + dedupe keys guarantee each reminder is sent once.
    Returns the number of reminders created (0 when nothing was due).
    """
    try:
        from server.apps.assignments.notifications import send_deadline_reminders
        return send_deadline_reminders()
    except Exception:
        log.exception("assignment deadline reminder scan failed")
        return 0


def run_forever():
    global _last_assignment_scan
    last_slow = 0.0
    while True:
        tick_all()
        if time.time() - _last_assignment_scan > ASSIGNMENT_REMINDER_EVERY:
            _last_assignment_scan = time.time()
            tick_assignments()
        if time.time() - last_slow > 60:
            last_slow = time.time()
            for uid in presence.user_ids():
                store = get_store(uid)
                try:
                    if not policy.is_blocked(uid):
                        maybe_daily_summary(store, lambda msg, uid=uid: notifier.push(uid, msg))
                    if time.time() - _state.setdefault(uid, {}).get("purged", 0) > 6 * 3600:
                        recorder_for(store).purge_old()
                        _state[uid]["purged"] = time.time()
                except Exception:
                    log.exception("slow job failed")
        time.sleep(1)
