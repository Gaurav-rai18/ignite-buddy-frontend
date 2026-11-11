"""Core types of the deterministic command engine."""
from dataclasses import dataclass
from typing import Callable

SAFE, CONFIRM, BLOCKED = "safe", "confirm", "blocked"      # runs silently | user must approve | never runs
SERVER, DEVICE = "server", "device"                         # where the tool executes


class ToolError(Exception):
    """A tool could not do what was asked (message is shown to the user)."""


class Ambiguous(Exception):
    """Several close matches: the executor asks the user to pick one, then calls finish(choice)."""
    def __init__(self, question: str, options: list[str], finish=None):
        super().__init__(question)
        self.question, self.options, self.finish = question, options, finish


# --- raised by grammar rules while parsing ---
class NoMatch(Exception):
    """This rule does not apply; try the next one."""


class Incomplete(Exception):
    """The sentence is clearly this command but a required detail is missing: ask for it."""
    def __init__(self, question: str):
        super().__init__(question)
        self.question = question


class Refuse(Exception):
    """The sentence asks for something policy never allows."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass
class Tool:
    name: str
    level: str
    doc: str
    args: dict                              # {"name": "str" | "str?"}; "?" = optional
    fn: Callable | None = None              # SERVER tools: fn(session, **args) -> {"msg": ..., ...}
    where: str = SERVER                     # DEVICE tools have no fn: they run on the client
    describe: Callable | None = None        # (session, **args) -> confirmation title
    preview: Callable | None = None         # (session, **args) -> extra detail for the confirmation card
    capability: str | None = None           # admin switch, e.g. 'files.delete' (see core/policy.py)
