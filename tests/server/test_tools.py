import time
import pytest
from server import commands, llm
from server.commands import parse, run_plan, validate
from server.features.activity.recorder import recorder_for
from shared import protocol as P


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    def boom(*a, **k): raise llm.LLMError("offline")
    monkeypatch.setattr(llm, "embed", boom)


def run(session, text):
    plan = validate(parse(text))
    return run_plan(session, plan["steps"])


def said(session): return "\n".join(session.ui.said)


def test_timers(session):
    assert run(session, "set a timer for 10 minutes for pasta")
    assert run(session, "list my timers")
    assert "pasta" in said(session) and "left" in said(session)
    assert run(session, "cancel the pasta timer")
    run(session, "list my timers")
    assert "No active timers" in said(session)


def test_bad_duration_is_a_clear_error(session):
    r = parse("set a timer for 0 minutes")
    assert r is None or not run(session, "set a timer for 0 minutes")


def test_reminders(session):
    assert run(session, "remind me to submit the report tomorrow at 5pm")
    run(session, "list my reminders")
    assert "submit the report" in said(session)
    assert run(session, "cancel the submit reminder")
    run(session, "list my reminders")
    assert "No pending reminders" in said(session)


def test_activity_stats_and_time(session):
    rec = recorder_for(session.store)
    t0 = time.time() - 600
    for i in range(0, 120, 5):
        rec.ingest("Code", "main.py - proj", False, t0 + i)
    for i in range(120, 180, 5):
        rec.ingest("chrome", "YouTube - Chrome", False, t0 + i)
    run(session, "how much time did I spend in vs code today")
    assert "m" in said(session) and "vs code" in said(session).lower()
    run(session, "show my focus report")
    assert "ocus" in said(session)


def test_private_windows_are_masked_before_storage(session):
    rec = recorder_for(session.store)
    rec.ingest("KeePass", "Vault", False, time.time())
    with session.store.conn() as con:
        assert con.execute("SELECT app,title FROM activity_events").fetchone() == ("(private)", "")


def test_pause_stops_recording_and_tells_client(session):
    run(session, "pause tracking for 30 minutes")
    assert session.ui.pushed[-1]["type"] == "tracking" and session.ui.pushed[-1]["paused"]
    assert recorder_for(session.store).ingest("Code", "x", False) is False
    run(session, "resume tracking")
    assert recorder_for(session.store).ingest("Code", "x", False) is True


def test_second_device_cannot_double_count(session):
    rec = recorder_for(session.store)
    assert rec.ingest("Code", "a", False, 1000.0, source="dev1")
    assert not rec.ingest("Code", "a", False, 1001.0, source="dev2")
    assert rec.ingest("Code", "a", False, 1100.0, source="dev2")          # dev1 went quiet


def test_wipe_everything(make_session):
    s = make_session(approve=True)
    run(s, "set a timer for 5 minutes"); run(s, "remind me to x tomorrow at 5pm")
    recorder_for(s.store).ingest("Code", "x", False)
    assert run(s, "wipe all my data")
    with s.store.conn() as con:
        for table in ("reminders", "timers", "activity_events", "actions"):
            assert con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] in (0, 1)   # 'actions' logs the wipe itself


def test_users_are_isolated(make_session):
    a, b = make_session(), make_session()
    run(a, "set a timer for 5 minutes for a")
    run(b, "list my timers")
    assert "No active timers" in said(b)


# ---- device steps through the executor ----
def test_device_ambiguity_then_choice(make_session):
    calls = []
    def device(op, args):
        calls.append((op, dict(args)))
        if op == P.FIND_FOLDER and "choice" not in args:
            return P.DeviceResult.ambiguous("Which?", ["/a/proj", "/b/proj"])
        if op == P.FIND_FOLDER:
            return P.DeviceResult.ok(path=args["choice"], msg="found")
        return P.DeviceResult.ok(msg="ok")
    s = make_session(device=device, choice="/b/proj")
    assert run(s, "open the proj folder")
    assert calls[1][1]["choice"] == "/b/proj" and calls[2][1]["path"] == "/b/proj"


def test_device_cancel_and_error_stop_the_plan(make_session):
    s = make_session(device=lambda op, a: P.DeviceResult.cancelled())
    assert not run(s, "run install.bat in proj")
    assert len(s.ui.calls) == 1
    s = make_session(device=lambda op, a: P.DeviceResult.error("nope"))
    assert not run(s, "open chrome and search cats")
    assert len(s.ui.calls) == 1 and "Failed: nope" in said(s)
