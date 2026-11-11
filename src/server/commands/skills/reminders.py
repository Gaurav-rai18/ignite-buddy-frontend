"""Reminders: set / list / cancel. The time phrase is located and parsed in code (util/timeparse)."""
from server.features import personal
from server.util import timeparse
from ..model import Incomplete, NoMatch, SAFE, ToolError
from ..parser import rule
from ..pick import pick
from ..registry import tool
from . import _native


# ---------------- tools ----------------
@tool("set_reminder", SAFE,
      "Set a reminder. when = time phrase as the user said it ('tomorrow at 5pm', 'in 2 hours'). "
      "repeat = '', 'daily' or 'weekly'.", {"text": "str", "when": "str", "repeat": "str?"})
def set_reminder(s, text, when, repeat=""):
    repeat = (repeat or "").lower().strip()
    if repeat not in ("", "daily", "weekly"):
        raise ToolError("Repeat must be daily or weekly.")
    try:
        due = timeparse.parse_when(when)
    except ValueError as e:
        raise ToolError(str(e))
    rid = personal.add_reminder(s.store, text, due, repeat)
    native = _native.mirror(s, "reminders", "reminder", rid, due.timestamp(), text, repeat)
    return {"msg": f"Reminder set for {personal.fmt_dt(due.timestamp())}: {text}" +
                   (f" (repeats {repeat})" if repeat else "") +
                   (" - Windows will alert you even if this app is closed." if native else "")}


@tool("list_reminders", SAFE, "List pending reminders.", {})
def list_reminders(s):
    rows = personal.pending_reminders(s.store)
    if not rows:
        return {"msg": "No pending reminders."}
    return {"msg": "\n".join(f"• {personal.fmt_dt(due)}: {text}" + (f" ({rep})" if rep else "")
                             for _, text, due, rep in rows)}


@tool("cancel_reminder", SAFE, "Cancel a reminder (query = words from its text, optional).", {"query": "str?"})
def cancel_reminder(s, query=""):
    def finish(row):
        _native.unmirror(s, "reminders", "reminder", row[0])
        personal.cancel_reminder(s.store, row[0])
        return {"msg": f"Cancelled reminder: {row[1]}"}
    return pick(personal.pending_reminders(s.store), query, lambda r: r[1],
                lambda r: f"#{r[0]} {r[1]} ({personal.fmt_dt(r[2])})", finish)


# ---------------- grammar ----------------
def _remind(rest, b):
    try:
        text, when, repeat = timeparse.split_when(rest)
    except ValueError:
        raise Incomplete("When should I remind you? For example: 'tomorrow at 5pm' or 'in 20 minutes'.")
    b.add("set_reminder", text=text, when=when, repeat=repeat or None)


@rule(r"remind me\s+(?:to\s+|about\s+|that\s+)?(?P<rest>.+)",
      examples=("remind me to submit the assignment tomorrow at 5pm", "remind me every day at 9am to log my hours",
                "remind me in 1 minute to stretch"))
def remind_me(m, b):
    _remind(m.group("rest"), b)


@rule(r"(?:set|add|create|make)(?:\s+a)?\s+reminder\s+(?:to\s+|for\s+|about\s+)(?P<rest>.+)")
def set_reminder_rule(m, b):
    _remind(m.group("rest"), b)


@rule(r"(?:list|show|what are|what's)(?:\s+me)?(?:\s+(?:my|the|all))?(?:\s+(?:pending|upcoming|active))?\s+reminders",
      examples=("list my reminders",))
def reminders_list(m, b):
    b.add("list_reminders")


@rule(r"(?:cancel|delete|remove)(?:\s+(?:my|the))?\s+reminder(?:\s+(?:about|to|for|called))?(?:\s+(?P<q>.+))?",
      examples=("cancel the reminder about stretch",))
def reminder_cancel(m, b):
    b.add("cancel_reminder", query=m.group("q"))


@rule(r"(?:cancel|delete|remove)(?:\s+(?:my|the))?\s+(?P<q>.+?)\s+reminder")
def reminder_cancel_named(m, b):
    b.add("cancel_reminder", query=m.group("q"))
