"""To-do list as a markdown checklist (Documents/TraineeAssistant/Tasks.md) on the trainee's PC."""
import re

from shared import protocol as P
from ..model import SAFE
from ..parser import rule
from ..registry import device_tool

device_tool(P.ADD_TASK, SAFE, "Add a to-do item.", {"text": "str"})
device_tool(P.LIST_TASKS, SAFE, "Show the to-do list.", {})
device_tool(P.COMPLETE_TASK, SAFE, "Tick off a to-do item.", {"query": "str"})
device_tool(P.DELETE_TASK, SAFE, "Remove a to-do item.", {"query": "str"})


@rule(r"(?:add|create|new)(?:\s+a)?\s+(?:task|todo|to-do)(?:\s+to)?\s*[:,\-]?\s*(?P<t>.+)"
      r"|add\s+(?P<t2>.+?)\s+to\s+my\s+(?:to-?do(?:\s+list)?|tasks?(?:\s+list)?)",
      examples=("add a task finish the react assignment", "add buy a notebook to my todo list"))
def add(m, b):
    b.add(P.ADD_TASK, text=(m.group("t") or m.group("t2")).strip())


@rule(r"(?:list|show|what are|what's on)(?:\s+me)?(?:\s+(?:my|the))?\s+(?:tasks|todos|to-dos|to-?do list|todo list|task list)",
      examples=("show my tasks",))
def list_(m, b):
    b.add(P.LIST_TASKS)


@rule(r"(?:complete|finish|check off|tick off)(?:\s+the)?\s+task\s+(?P<q>.+)"
      r"|mark(?:\s+the)?(?:\s+task)?\s+(?P<q2>.+?)\s+(?:as\s+)?(?:done|complete|completed)",
      examples=("complete task react assignment", "mark the notebook task as done"))
def complete(m, b):
    b.add(P.COMPLETE_TASK, query=re.sub(r"\s+task$", "", (m.group("q") or m.group("q2")).strip(), flags=re.I))


@rule(r"(?:delete|remove)(?:\s+the)?\s+task\s+(?P<q>.+)|remove\s+(?P<q2>.+?)\s+from\s+my\s+(?:to-?do(?:\s+list)?|tasks?(?:\s+list)?)",
      examples=("delete task notebook",))
def delete(m, b):
    b.add(P.DELETE_TASK, query=(m.group("q") or m.group("q2")).strip())
