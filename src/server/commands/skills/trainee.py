"""Programme data on the trainee's PC (local SQLite): assignments, weekly timetable, command history, chat history.
Assignments and the timetable are published by the admin panel and synced to the PC; the trainee tracks status locally."""
from shared import protocol as P
from ..model import CONFIRM, SAFE
from ..parser import rule
from ..registry import device_tool

device_tool(P.LIST_ASSIGNMENTS, SAFE, "List assignments (pending, all, done, week).", {"filter": "str?"})
device_tool(P.NEXT_ASSIGNMENT, SAFE, "Say which assignment is due next.", {})
device_tool(P.SET_ASSIGNMENT, SAFE, "Mark an assignment done or pending.", {"query": "str", "status": "str"})
device_tool(P.SHOW_TIMETABLE, SAFE, "Show the timetable for a day or the week.", {"day": "str?"})
device_tool(P.NEXT_CLASS, SAFE, "Say what the next class is.", {})
device_tool(P.SHOW_AUDIT, SAFE, "List the commands recently run on this PC.", {})
device_tool(P.CLEAR_AUDIT, CONFIRM, "Clear the command history (the PC asks first).", {})
device_tool(P.CLEAR_CHAT, CONFIRM, "Forget the remembered conversation (the PC asks first).", {})

_DAY = r"(?:today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|this week|the week|week|weekly)"
_DONE = r"(?:done|complete|completed|finished|submitted)"


@rule(r"when is my next assignment(?: due)?|what(?:'s| is) my next assignment|what(?:'s| is) due next",
      examples=("when is my next assignment due",))
def next_assignment(m, b):
    b.add(P.NEXT_ASSIGNMENT)


@rule(rf"(?:what|which)(?: are| is)?(?: my| the)?(?: (?P<f>pending|upcoming|completed|done))? assignments?(?: (?:do i have|are there|are|is))?(?: (?:due|pending|due soon))?(?: (?P<w>this week))?"
      rf"|(?:list|show|give)(?: me)?(?: my| the| all)?(?: (?P<f2>pending|upcoming|completed|done|all))? assignments(?: (?P<w2>due this week))?"
      rf"|(?:do i have|are there)(?: any)?(?: pending| upcoming)? assignments(?: due)?(?: (?P<w3>this week))?",
      examples=("what assignments are due", "show my pending assignments", "list all assignments"))
def list_assignments(m, b):
    g = m.groupdict()
    flt = g.get("f") or g.get("f2") or "pending"
    if g.get("w") or g.get("w2") or g.get("w3"):
        flt = "week"
    b.add(P.LIST_ASSIGNMENTS, filter={"upcoming": "pending", "completed": "done"}.get(flt, flt))


@rule(rf"mark(?: the)? assignment (?P<q>.+?) (?:as )?{_DONE}|mark(?: the)? (?P<q2>.+?) assignment (?:as )?{_DONE}"
      rf"|(?:i |i have |i've )?(?:submitted|finished|completed)(?: the)? (?P<q3>.+?) assignment",
      examples=("mark the react assignment as done", "I submitted the java assignment"))
def done(m, b):
    b.add(P.SET_ASSIGNMENT, query=(m.group("q") or m.group("q2") or m.group("q3")).strip(), status="done")


@rule(r"(?:reopen|unmark)(?: the)? (?P<q>.+?) assignment|mark(?: the)? (?P<q2>.+?) assignment (?:as )?(?:pending|not done|incomplete)",
      examples=("reopen the react assignment",))
def reopen(m, b):
    b.add(P.SET_ASSIGNMENT, query=(m.group("q") or m.group("q2")).strip(), status="pending")


@rule(rf"what(?:'s| is) my next (?:class|session|lecture|slot|lab)|when is my next (?:class|session|lecture|slot|lab)"
      rf"|where (?:do|should) i (?:sit|go|be)(?: right)?(?: now)?"
      rf"|where is my (?:class|session|lecture|lab|stream|seat)(?: right)?(?: now)?"
      rf"|where am i supposed to (?:sit|go|be)"
      rf"|what (?:class|session|lecture|lab) (?:do i have|is there|is next)(?: right)?(?: now)?"
      rf"|what am i having right now",
      examples=("what is my next class", "where should I sit", "where is my lecture", "where do I sit right now"))
def next_class(m, b):
    b.add(P.NEXT_CLASS)


@rule(rf"(?:(?:what(?:'s| is)|show|give|display|open|view|get|check|see)(?: me)?(?: my)?\s+|my\s+)?(?:timetable|time table|schedule|classes|lectures)(?: (?:for|on))?(?: (?P<d>{_DAY}))?"
      rf"|what(?:'s| is) on(?: my timetable| my schedule)?(?: (?P<d2>{_DAY}))?"
      rf"|do i have (?:any )?(?:class|classes|sessions?|lectures?|tests?|exams?)(?: (?P<d3>today|tomorrow|this week))?"
      rf"|show (?:my )?stream schedule",
      examples=("what is my timetable today", "show my schedule", "show schedule", "what is my schedule", "schedule for friday", "do I have class tomorrow"))
def timetable(m, b):
    d = m.group("d") or m.group("d2") or m.group("d3")
    b.add(P.SHOW_TIMETABLE, day=(d or "today").replace("the week", "week").replace("this week", "week"))


@rule(r"(?:show|list)(?: me)?(?: my)? (?:command|action) (?:history|log)|what (?:did you|have you) (?:do|done)(?: (?:today|recently))?",
      examples=("show my command history",))
def audit(m, b):
    b.add(P.SHOW_AUDIT)


@rule(r"clear(?: my)? (?:command|action) (?:history|log)", examples=("clear my command history",))
def clear_audit(m, b):
    b.add(P.CLEAR_AUDIT)


@rule(r"(?:forget|clear)(?: (?:our|this|my))? (?:conversation|chat)(?: history)?", examples=("forget our conversation",))
def clear_chat(m, b):
    b.add(P.CLEAR_CHAT)
