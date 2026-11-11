"""Everyday trainee helpers. All deterministic; some run on the server (calculator), some on the PC (Windows)."""
import ast
import json
import operator
import os
import re

from shared import protocol as P
from server.util import timeparse
from ..model import CONFIRM, Incomplete, NoMatch, SAFE, ToolError
from ..parser import rule
from ..registry import device_tool, tool

device_tool(P.OPEN_SYSTEM, SAFE, "Open a built-in Windows app, Settings page or well-known folder.", {"target": "str"},
            capability="system.open")
device_tool(P.LOCK_SCREEN, SAFE, "Lock the computer.", {}, capability="system.lock")
device_tool(P.CLIPBOARD_SET, SAFE, "Put text on the clipboard.", {"text": "str"}, capability="clipboard.write")
device_tool(P.GET_TIME, SAFE, "Say the current date and time on the PC.", {})

# ------------------------------- calculator (server, no model) -------------------------------
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}


def _eval(node, depth=0):
    if depth > 20:
        raise ValueError("too deep")
    if isinstance(node, ast.Expression):
        return _eval(node.body, depth + 1)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _eval(node.operand, depth + 1)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        a, b = _eval(node.left, depth + 1), _eval(node.right, depth + 1)
        if isinstance(node.op, ast.Pow) and (abs(b) > 100 or abs(a) > 1e6):
            raise ValueError("too large")
        return _OPS[type(node.op)](a, b)
    raise ValueError("unsupported")


_WORDS = [(r"\bto the power of\b", "**"), (r"\bmultiplied by\b|\btimes\b|×", "*"), (r"\bdivided by\b|\bover\b|÷", "/"),
          (r"\bplus\b", "+"), (r"\bminus\b", "-"), (r"\bmod(?:ulo)?\b", "%"), (r"\^", "**"), (r"(?<=\d)\s*x\s*(?=\d)", "*")]


def to_expression(text: str) -> str:
    t = text.lower().replace(",", "")
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s+of\s+(\d+(?:\.\d+)?)", r"(\1/100*\2)", t)
    for pat, rep in _WORDS:
        t = re.sub(pat, rep, t)
    t = t.strip()
    if not re.fullmatch(r"[\d\s.+\-*/()%]+", t) or not re.search(r"\d", t) or not re.search(r"[+\-*/%]", t.lstrip("-+ ")):
        raise NoMatch
    return t


def _fmt(v) -> str:
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        v = int(v)
    return f"{v:,}" if isinstance(v, int) else f"{v:,.6g}"


@tool("calculate", SAFE, "Evaluate an arithmetic expression (no model).", {"expression": "str"})
def calculate(s, expression):
    try:
        tree = ast.parse(expression, mode="eval")
        return {"msg": f"{expression.strip()} = {_fmt(_eval(tree))}"}
    except ZeroDivisionError:
        raise ToolError("That divides by zero.")
    except (ValueError, SyntaxError, OverflowError, RecursionError):
        raise ToolError("I couldn't calculate that.")


@rule(r"(?:calculate|compute|calc|solve|what(?:'s| is)|how much is|whats)\s+(?P<e>.+)", examples=("what is 15% of 240", "calculate 12 * (3 + 4)"))
def calc(m, b):
    b.add("calculate", expression=to_expression(m.group("e")))


# ------------------------------- time, alarm, focus sessions -------------------------------
@rule(r"what(?:'s| is)? (?:the )?(?:current )?(?:time|date)(?: (?:now|today|is it))?|what time is it|what day is (?:it|today)"
      r"|what(?:'s| is) today'?s date|current (?:time|date)", examples=("what time is it",))
def time_now(m, b):
    b.add(P.GET_TIME)


@rule(r"(?:set|create|add)(?:\s+an?)?\s+alarm(?:\s+(?:for|at|to ring at))?\s+(?P<rest>.+)", examples=("set an alarm for 7am",))
def alarm(m, b):
    try:
        _, when, repeat = timeparse.split_when("Alarm " + m.group("rest"))
    except ValueError:
        raise Incomplete("What time should the alarm ring? For example 'set an alarm for 7am'.")
    b.add("set_reminder", text="Alarm", when=when, repeat=repeat or None)


@rule(r"(?:start|set|begin)(?:\s+a)?\s+pomodoro(?:\s+(?:timer|session))?", examples=("start a pomodoro",))
def pomodoro(m, b):
    b.add("set_timer", duration="25 minutes", label="Pomodoro: focus time is over, take a 5 minute break")
    b.add("set_timer", duration="30 minutes", label="Pomodoro: break is over, back to work")


@rule(r"(?:start|begin)(?:\s+a)?\s+(?:focus|study)\s+session(?:\s+(?:for|of)\s+(?P<d>.+))?", examples=("start a focus session for 45 minutes",))
def focus_session(m, b):
    d = m.group("d") or "25 minutes"
    try:
        timeparse.parse_duration(d)
    except ValueError:
        raise Incomplete("For how long? For example '45 minutes'.")
    b.add("set_timer", duration=d, label="Focus session is over")


# ------------------------------- Windows: apps, settings, folders, lock, clipboard -------------------------------
@rule(r"(?:open|launch|start)(?:\s+(?:the|my))?\s+(?P<t>calculator|calc|notepad|paint|task manager|command prompt|cmd|terminal|"
      r"file explorer|explorer|snipping tool|screenshot tool|clock|clock app|alarms?(?: app)?|calendar|camera)(?:\s+app)?",
      examples=("open task manager", "open the clock app"))
def open_builtin(m, b):
    b.add(P.OPEN_SYSTEM, target=m.group("t").strip())


@rule(r"(?:open|show|go to)(?:\s+(?:the|my))?\s+(?P<t>wi-?fi|network|bluetooth|display|sound|battery|storage|windows update|update|apps|privacy|date and time|time)\s+settings",
      examples=("open wifi settings",))
def open_settings(m, b):
    b.add(P.OPEN_SYSTEM, target=m.group("t").lower() + " settings")


@rule(r"(?:open|go to|show)(?:\s+(?:the|my))?\s+(?P<t>downloads|documents|desktop)(?:\s+folder)?", examples=("open my downloads",))
def open_known_folder(m, b):
    b.add(P.OPEN_SYSTEM, target=m.group("t"))


@rule(r"(?:take|grab|capture)(?:\s+a)?\s+screenshot", examples=("take a screenshot",))
def screenshot(m, b):
    b.add(P.OPEN_SYSTEM, target="snipping tool")


@rule(r"lock(?:\s+(?:my|the))?(?:\s+(?:computer|pc|laptop|screen|workstation))?", examples=("lock my computer",))
def lock(m, b):
    b.add(P.LOCK_SCREEN)


@rule(r"copy\s+(?P<t>.+?)\s+to\s+(?:the\s+|my\s+)?clipboard", examples=("copy npm install to clipboard",))
def clipboard(m, b):
    b.add(P.CLIPBOARD_SET, text=m.group("t").strip().strip("\"'"))


# ------------------------------- quick links (admin can extend with ASSISTANT_QUICK_SITES='{"intranet": "https://..."}') -------------------------------
SITES = {"youtube": "https://www.youtube.com", "github": "https://github.com", "stackoverflow": "https://stackoverflow.com",
         "stack overflow": "https://stackoverflow.com", "gmail": "https://mail.google.com", "google": "https://www.google.com",
         "linkedin": "https://www.linkedin.com", "leetcode": "https://leetcode.com", "w3schools": "https://www.w3schools.com",
         "mdn": "https://developer.mozilla.org", "chatgpt": "https://chatgpt.com", "claude": "https://claude.ai"}
try:
    SITES.update({k.lower(): v for k, v in json.loads(os.getenv("ASSISTANT_QUICK_SITES", "{}")).items()})
except ValueError:
    pass


@rule(r"(?:open|go to|visit)(?:\s+the)?\s+(?P<s>[a-z0-9 ]+?)(?:\s+(?:website|site|page))?")
def quick_site(m, b):
    url = SITES.get(m.group("s").strip().lower())
    if not url:
        raise NoMatch
    b.add(P.OPEN_URL, url=url)
