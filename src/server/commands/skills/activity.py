"""Activity tracking controls and INSTANT statistics (all numbers come from code, no model)."""
from datetime import datetime

from server.features.activity import sessionize, summarize, usage
from server.features.activity.recorder import recorder_for
from server.util import timeparse
from server.util.timeparse import PERIOD
from ..model import CONFIRM, Incomplete, SAFE, ToolError
from ..parser import rule
from ..registry import tool


def _tell_client(s, rec):
    """The client stops sampling while paused, so nothing leaves the machine."""
    s.ui.push({"type": "tracking", **rec.pause_state()})


# ---------------- tools ----------------
@tool("pause_tracking", SAFE, "Pause activity tracking, optionally for a duration like '30 minutes'.",
      {"duration": "str?"})
def pause_tracking(s, duration=""):
    secs = None
    if (duration or "").strip():
        try:
            secs = timeparse.parse_duration(duration)
        except ValueError:
            raise ToolError(f"I couldn't understand the duration '{duration}'.")
    rec = recorder_for(s.store)
    rec.pause(secs)
    _tell_client(s, rec)
    return {"msg": "Activity tracking paused" + (f" for {timeparse.fmt_duration(secs)}." if secs else
                                                 " until you resume it.")}


@tool("resume_tracking", SAFE, "Resume activity tracking.", {})
def resume_tracking(s):
    rec = recorder_for(s.store)
    rec.resume()
    _tell_client(s, rec)
    return {"msg": "Activity tracking resumed."}


@tool("tracking_status", SAFE, "Say whether activity tracking is on.", {})
def tracking_status(s):
    return {"msg": "Activity tracking is paused." if recorder_for(s.store).is_paused() else "Activity tracking is on."}


@tool("focus_report", SAFE, "Instant statistics (time per category/app, focus %) for a period. No AI.",
      {"when": "str?"})
def focus_report(s, when="today"):
    start, end, label = timeparse.parse_range(when or "today")
    events = summarize.load_events(s.store, start.timestamp(), end.timestamp())
    _, stats = sessionize.analyze(events)
    return {"msg": sessionize.format_stats(f"Focus report for {label}", stats)}


@tool("activity_time", SAFE, "Time spent in an app, category (coding, browsing...) or window title, for a period. No AI.",
      {"subject": "str", "when": "str?"})
def activity_time(s, subject, when="today"):
    label, matched, total = usage.usage(s.store, subject, when)
    if not total:
        return {"msg": f"I have no recorded activity for {label}."}
    if not matched:
        return {"msg": f"I have no record of '{subject}' for {label}."}
    return {"msg": f"{subject}: {timeparse.fmt_duration(matched)} {label} "
                   f"({matched / total * 100:.0f}% of {timeparse.fmt_duration(total)} active)."}


def _range(when):
    if (when or "").strip().lower() in ("all", "everything"):
        return datetime.fromtimestamp(0), datetime(2100, 1, 1), "all recorded activity"
    return timeparse.parse_range(when or "today")


def _delete_describe(s, when):
    return f"Permanently delete recorded activity for: {_range(when)[2]}"


def _delete_preview(s, when):
    a, e, _ = _range(when)
    with s.store.conn() as con:
        n = con.execute("SELECT COUNT(*) FROM activity_events WHERE end_ts>? AND start_ts<?",
                        (a.timestamp(), e.timestamp())).fetchone()[0]
    return f"{n} activity records (and any daily summaries in this period) will be deleted."


@tool("delete_activity", CONFIRM, "Delete recorded activity data for a period ('today', 'last hour', 'all').",
      {"when": "str"}, describe=_delete_describe, preview=_delete_preview)
def delete_activity(s, when):
    a, e, label = _range(when)
    with s.store.conn() as con:
        con.execute("DELETE FROM activity_events WHERE end_ts>? AND start_ts<?", (a.timestamp(), e.timestamp()))
        con.execute("DELETE FROM summaries WHERE start_ts>=? AND end_ts<=?", (a.timestamp(), e.timestamp()))
    recorder_for(s.store).reset()
    return {"msg": f"Deleted activity data for {label}."}


# ---------------- grammar ----------------
@rule(r"(?:pause|stop|disable|turn off)(?:\s+my)?(?:\s+activity)?\s+tracking(?:\s+for\s+(?P<d>.+))?",
      examples=("pause tracking", "pause tracking for 30 minutes"))
def pause(m, b):
    d = m.group("d")
    if d:
        try:
            timeparse.parse_duration(d)
        except ValueError:
            raise Incomplete("For how long? For example '30 minutes', or say 'pause tracking' to pause until you resume.")
    b.add("pause_tracking", duration=d)


@rule(r"(?:resume|start|continue|enable|restart|turn on)(?:\s+my)?(?:\s+activity)?\s+tracking", examples=("resume tracking",))
def resume(m, b):
    b.add("resume_tracking")


@rule(r"(?:is\s+)?(?:activity\s+)?tracking\s+(?:on|paused|running|enabled|status)|am i being tracked",
      examples=("tracking status",))
def status(m, b):
    b.add("tracking_status")


@rule(rf"(?:show|give|get)(?:\s+me)?(?:\s+(?:my|the))?\s+(?:focus|productivity)\s+(?:report|stats|statistics)"
      rf"(?:\s+(?:for|of|in|on|over|during))?(?:\s+(?P<w>{PERIOD}))?"
      rf"|how\s+(?:focused|productive)\s+(?:was|am|have been)\s+i(?:\s+(?:for|in|on|over|during))?(?:\s+(?P<w2>{PERIOD}))?",
      examples=("show my focus report for yesterday", "how focused was I today"))
def focus(m, b):
    b.add("focus_report", when=m.group("w") or m.group("w2"))


@rule(rf"how\s+(?:much time|long)(?:\s+(?:have|did|do))?\s+i\s+(?:spend|spent|use|used|work|worked|been)"
      rf"(?:\s+(?:in|on|with|using))?\s+(?P<subj>.+?)(?:\s+(?:for\s+|in\s+|on\s+)?(?P<w>{PERIOD}))?",
      examples=("how much time did I spend in VS Code today",))
def app_time(m, b):
    b.add("activity_time", subject=m.group("subj").strip(), when=m.group("w"))


@rule(rf"(?:delete|clear|erase|remove|wipe)(?:\s+(?:my|the|all))?(?:\s+(?P<w>today'?s|yesterday'?s|all))?\s+activity"
      rf"(?:\s+(?:data|history|records|log))?(?:\s+(?:for|from|of)\s+(?P<w2>{PERIOD}|all|everything))?",
      examples=("delete today's activity",))
def delete(m, b):
    w = m.group("w") or m.group("w2")
    if not w:
        raise Incomplete("For which period? For example 'today', 'yesterday', 'last hour' or 'all'.")
    w = w.lower().replace("'s", "").replace("s'", "")
    b.add("delete_activity", when=w)
