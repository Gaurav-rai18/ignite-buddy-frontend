import pytest
from server import commands
from server.commands import parse, run_plan, validate
from server.domain import policy
from server.features import personal
from server.jobs import runner
from shared import protocol as P
import time


def run(session, text):
    return run_plan(session, validate(parse(text))["steps"])


def said(s): return "\n".join(s.ui.said)


def test_delete_is_off_by_default_and_admin_can_enable(make_session):
    calls = []
    s = make_session(device=lambda op, a: calls.append(op) or P.DeviceResult.ok(path="/x/old.txt", msg="ok"))
    assert not run(s, "delete the file old.txt")
    assert "administrator" in said(s) and "files.delete" in said(s) and calls == ["find_file"]
    policy.set_capability("files.delete", True, user_id=s.user.id)
    try:
        assert run(s, "delete the file old.txt") and calls[-1] == "delete_path"
    finally:
        policy.set_capability("files.delete", False, user_id=s.user.id)


def test_capability_sources(tmp_path, monkeypatch):
    f = tmp_path / "p.json"
    f.write_text('{"default": {"files.move": false}, "users": {"alice": {"files.delete": true}}}')
    monkeypatch.setenv("ASSISTANT_POLICY_FILE", str(f)); monkeypatch.setenv("ASSISTANT_CAPABILITIES", "system.lock=off")
    policy.load_capabilities()
    try:
        assert not policy.allows("files.move") and not policy.allows("system.lock") and policy.allows("files.create")
        assert policy.allows("files.delete", "alice") and not policy.allows("files.delete", "bob")
        assert not policy.allows("made.up.capability")                       # unknown = denied
    finally:
        monkeypatch.delenv("ASSISTANT_POLICY_FILE"); monkeypatch.delenv("ASSISTANT_CAPABILITIES")
        policy.load_capabilities()


def test_disabled_capability_blocks_device_call(make_session):
    calls = []
    s = make_session(device=lambda op, a: calls.append(op) or P.DeviceResult.ok(msg="ok"))
    policy.set_capability("system.lock", False, user_id=s.user.id)
    try:
        assert not run(s, "lock my computer") and calls == []
    finally:
        policy.set_capability("system.lock", True, user_id=s.user.id)


def test_help_lists_what_is_switched_off(session):
    run(session, "help")
    assert "files.delete" in said(session)


# ---------------- native timers/reminders ----------------
def native_ok(calls):
    def device(op, args):
        calls.append((op, dict(args)))
        return P.DeviceResult.ok(msg="Scheduled in Windows.")
    return device


def test_timer_and_reminder_are_mirrored_into_windows(make_session):
    calls = []
    s = make_session(device=native_ok(calls))
    assert run(s, "set a timer for 10 minutes for pasta")
    op, a = calls[0]
    assert op == P.NATIVE_SCHEDULE and a["kind"] == "timer" and a["text"] == "pasta" and abs(int(a["at"]) - (time.time() + 600)) < 5
    assert "Windows will alert you" in said(s)
    assert run(s, "remind me every day at 9am to log my hours")
    assert calls[1][1]["repeat"] == "daily" and calls[1][1]["kind"] == "reminder"
    assert personal.is_native(s.store, "timers", 1)


def test_native_ids_are_unique_per_user(make_session):
    a_calls, b_calls = [], []
    a, b = make_session(device=native_ok(a_calls)), make_session(device=native_ok(b_calls))
    run(a, "set a timer for 5 minutes"); run(b, "set a timer for 5 minutes")
    assert a_calls[0][1]["ref"] != b_calls[0][1]["ref"]


def test_cancel_removes_the_windows_task(make_session):
    calls = []
    s = make_session(device=native_ok(calls))
    run(s, "set a timer for 10 minutes for pasta")
    assert run(s, "cancel the pasta timer")
    assert calls[-1][0] == P.NATIVE_CANCEL and calls[-1][1]["ref"] == calls[0][1]["ref"]


def test_falls_back_to_server_notifications_when_native_unavailable(session):
    assert run(session, "set a timer for 1 minutes")            # FakeUI device errors -> not native
    assert not personal.is_native(session.store, "timers", 1) and "Windows will alert" not in said(session)
    sent = []
    runner.tick(session.store, sent.append, now=time.time() + 120)
    assert any("Timer finished" in m["text"] for m in sent)


def test_scheduler_does_not_double_notify_native_items(make_session):
    s = make_session(device=native_ok([]))
    run(s, "set a timer for 1 minutes")
    sent = []
    runner.tick(s.store, sent.append, now=time.time() + 120)
    assert sent == []                                            # Windows shows the toast; the server stays quiet
    assert personal.pending_timers(s.store) == []


def test_admin_can_disable_native_scheduling(make_session):
    calls = []
    s = make_session(device=native_ok(calls))
    policy.set_capability("native.schedule", False, user_id=s.user.id)
    try:
        run(s, "set a timer for 1 minutes")
        assert calls == []
    finally:
        policy.set_capability("native.schedule", True, user_id=s.user.id)


# ---------------- calculator / utilities (no device, no model) ----------------
@pytest.mark.parametrize("text,answer", [("what is 15% of 240", "36"), ("calculate 12 * (3 + 4)", "84"), ("what's 2 plus 2", "= 4"),
                                         ("what is 10 divided by 4", "2.5"), ("what is 2 to the power of 10", "1,024")])
def test_calculator(session, text, answer):
    assert run(session, text) and answer in said(session)


def test_calculator_is_safe_and_not_greedy(session):
    assert parse("what is a closure") is None and parse("what is python") is None
    assert parse("what is 5") is None
    assert not run(session, "calculate 1/0") and "divides by zero" in said(session)
    assert parse("calculate __import__('os').system('x')") is None
    assert not run(session, "calculate 9 ** 9 ** 9") or "couldn't" in said(session)


def test_pomodoro_and_alarm_plans():
    assert [s["tool"] for s in parse("start a pomodoro")["steps"]] == ["set_timer", "set_timer"]
    assert parse("set an alarm for 7am")["steps"][0]["args"] == {"text": "Alarm", "when": "7am"}
    assert parse("wipe all my data")["steps"][0]["tool"] == "wipe_all_data"
