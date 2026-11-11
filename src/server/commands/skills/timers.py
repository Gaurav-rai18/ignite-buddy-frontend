"""Timers: set / list / cancel. Durations are parsed in code (util/timeparse), never by a model."""
import time

from server.features import personal
from server.util import timeparse
from ..model import NoMatch, SAFE, ToolError
from ..parser import rule
from ..pick import pick
from ..registry import tool
from . import _native

_LABEL = r"(?:\s+(?:for|called|named|labell?ed|to)\s+(?P<label>.+))?"


# ---------------- tools ----------------
@tool("set_timer", SAFE, "Start a countdown timer. duration like '10 minutes'.", {"duration": "str", "label": "str?"})
def set_timer(s, duration, label=""):
    try:
        secs = timeparse.parse_duration(duration)
    except ValueError:
        raise ToolError(f"I couldn't understand the duration '{duration}'.")
    if not 1 <= secs <= 24 * 3600:
        raise ToolError("Timers must be between 1 second and 24 hours.")
    tid = personal.add_timer(s.store, secs, label)
    native = _native.mirror(s, "timers", "timer", tid, time.time() + secs, label or "Your timer is done")
    return {"msg": f"Timer set for {timeparse.fmt_duration(secs)}" + (f" ({label})" if label else "")
                   + (" - Windows will alert you even if this app is closed." if native else "")}


@tool("list_timers", SAFE, "List active timers.", {})
def list_timers(s):
    rows = personal.pending_timers(s.store)
    if not rows:
        return {"msg": "No active timers."}
    return {"msg": "\n".join(f"• {label or 'Timer'}: {timeparse.fmt_duration(max(0, end - time.time()))} left"
                             for _, label, end in rows)}


@tool("cancel_timer", SAFE, "Cancel a timer (query = its label, optional).", {"query": "str?"})
def cancel_timer(s, query=""):
    def finish(row):
        _native.unmirror(s, "timers", "timer", row[0])
        personal.cancel_timer(s.store, row[0])
        return {"msg": f"Cancelled timer {row[1] or '#' + str(row[0])}."}
    return pick(personal.pending_timers(s.store), query, lambda r: r[1] or "timer",
                lambda r: f"#{r[0]} {r[1] or 'timer'} ({timeparse.fmt_duration(max(0, r[2] - time.time()))} left)",
                finish)


# ---------------- grammar ----------------
def _timer(dur, label, b):
    try:
        timeparse.parse_duration(dur)
    except ValueError:
        raise NoMatch
    b.add("set_timer", duration=dur.strip(), label=(label or "").strip() or None)


@rule(rf"(?:set|start|create|begin)(?:\s+up)?(?:\s+an?)?\s+timer\s+(?:for\s+|of\s+)?(?P<dur>.+?){_LABEL}",
      examples=("set a timer for 10 minutes", "start a timer for 25 minutes for pomodoro"))
def timer_for(m, b):
    _timer(m.group("dur"), m.group("label"), b)


@rule(r"(?:set|start|create)(?:\s+an?)?\s+(?P<dur>[\w.\s-]+?)[\s-]timer(?:\s+(?:for|called|named)\s+(?P<label>.+))?",
      examples=("set a 10 minute timer for pasta",))
def timer_adjective(m, b):
    _timer(m.group("dur"), m.group("label"), b)


@rule(r"(?:set|start|create)(?:\s+an?)?\s+(?P<label>(?!an?\b)[\w\s-]+?)\s+timer\s+(?:for\s+|of\s+)(?P<dur>.+)",
      examples=("set a pasta timer for 10 minutes",))
def timer_labelled(m, b):
    _timer(m.group("dur"), m.group("label"), b)


@rule(r"(?:list|show|what are|what's|whats)(?:\s+me)?(?:\s+(?:my|the|all))?(?:\s+(?:active|running|current))?\s+timers"
      r"|how (?:much time|long)(?: is)? left(?: on| for)?(?: my| the)?(?: \w+)? timer"
      r"|(?:do i have|are there)(?: any)?(?: active| running)? timers(?: running)?",
      examples=("list my timers", "how much time is left on my timer"))
def timers_list(m, b):
    b.add("list_timers")


@rule(r"(?:cancel|stop|delete|remove|clear)(?:\s+(?:my|the))?(?:\s+(?P<q>.+?))?\s+timer",
      examples=("cancel the pasta timer", "stop my timer"))
def timer_cancel(m, b):
    b.add("cancel_timer", query=m.group("q"))


@rule(r"(?:cancel|stop|delete|remove)(?:\s+(?:my|the))?\s+timer\s+(?:for|called|named|about)\s+(?P<q>.+)")
def timer_cancel_named(m, b):
    b.add("cancel_timer", query=m.group("q"))
