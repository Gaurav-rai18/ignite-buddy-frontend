import time
from server.domain import policy
from server.features import personal
from server.jobs import runner
from datetime import datetime, timedelta


def test_reminder_timer_fire_and_repeat(session):
    personal.add_reminder(session.store, "once", datetime.now() - timedelta(seconds=5))
    personal.add_reminder(session.store, "daily", datetime.now() - timedelta(seconds=5), "daily")
    personal.add_reminder(session.store, "late", datetime.now() - timedelta(hours=3))
    personal.add_timer(session.store, 1)
    sent = []
    runner.tick(session.store, sent.append, now=time.time() + 2)
    texts = [m["text"] for m in sent]
    assert any("once" in t for t in texts) and any("(missed)" in t and "late" in t for t in texts)
    assert any("Timer finished" in t for t in texts)
    assert len(personal.pending_reminders(session.store)) == 1            # only the repeating one remains
    sent.clear()
    runner.tick(session.store, sent.append, now=time.time() + 2)
    assert sent == []                                                     # nothing fires twice


def test_blocked_user_gets_nothing(session):
    personal.add_reminder(session.store, "x", datetime.now() - timedelta(seconds=5))
    policy.set_blocked(True, user_id=session.user.id)
    try:
        sent = []
        runner.tick(session.store, sent.append)
        assert sent == []
    finally:
        policy.set_blocked(False, user_id=session.user.id)
    runner.tick(session.store, sent.append)
    assert sent


def test_policy_per_user():
    policy.set_blocked(True, user_id="u1")
    assert policy.is_blocked("u1") and not policy.is_blocked("u2")
    policy.set_blocked(False, user_id="u1")
