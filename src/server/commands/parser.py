"""
Deterministic command parser: sentence -> plan, with NO model call.

  1. Skills (commands/skills/*.py) register grammar rules with @rule(regex).  First rule that matches a clause wins;
     registration order = priority.  A rule may raise NoMatch (try the next), Incomplete (ask a question) or
     Refuse (policy).
  2. A sentence is split into clauses at "and / then / ," and each clause is parsed on its own, so
     "open the react assignment 3 in vs code and run install.bat" becomes a 3-step plan.  Free-text rules (notes,
     reminders, searches) are protected: a split is accepted only if EVERY part parses, otherwise the whole
     sentence is tried as one clause ("remind me to buy milk and eggs tomorrow at 5pm").
  3. State flows between clauses through the Builder (e.g. `run install.bat` reuses the folder opened before).

Same input -> same output, always.  Add a command = add a rule (see docs/ARCHITECTURE.md).
"""
import re
from dataclasses import dataclass
from typing import Callable

from .builder import Builder
from server.util.text import normalize_spoken
from .model import Incomplete, NoMatch, Refuse


@dataclass(frozen=True)
class Rule:
    pattern: re.Pattern
    fn: Callable
    examples: tuple
    group: str
    name: str


RULES: list[Rule] = []


def rule(pattern: str, *, examples=(), group: str = ""):
    """@rule(r"set a timer for (?P<dur>.+)")  -> fn(match, builder).  The pattern must match the WHOLE clause."""
    rx = re.compile(pattern, re.I)

    def deco(fn):
        RULES.append(Rule(rx, fn, tuple(examples), group or fn.__module__.rsplit(".", 1)[-1], fn.__name__))
        return fn
    return deco


_FILLER = re.compile(r"^(?:(?:hey|hi|ok|okay|please|assistant|computer)\b[\s,]*"
                     r"|(?:can|could|would|will) you(?: please)?\s+"
                     r"|i (?:want|need|would like) you to\s+|i'd like you to\s+|let's\s+)+", re.I)
_TRAIL = re.compile(r"[\s,]+(?:please|for me|now|thanks|thank you)$", re.I)
_CONJ = re.compile(r"(?:\s*[,;]\s*(?:and\s+)?(?:then\s+)?|\s+(?:and\s+then|and\s+also|and|then|after\s+that)\s+)", re.I)
_COMMAND_VERB = re.compile(r"^(?:open|launch|run|remind|cancel|pause|resume)\b", re.I)


def clean(clause: str) -> str:
    s = clause.strip().rstrip(".!?").strip()
    s = _FILLER.sub("", s)
    s = _TRAIL.sub("", s)
    return s.strip()


def _clause(text: str, b: Builder):
    s = clean(text)
    if not s:
        raise NoMatch
    for r in RULES:
        m = r.pattern.fullmatch(s)
        if not m:
            continue
        mark = b.mark()
        try:
            r.fn(m, b)
            return
        except NoMatch:
            b.rewind(mark)
        except (Incomplete, Refuse):
            b.rewind(mark)
            raise
    raise NoMatch


def _sequence(text: str, b: Builder):
    pending: Incomplete | None = None
    for m in _CONJ.finditer(text):
        left, right = text[:m.start()], text[m.end():]
        if not left.strip() or not right.strip():
            continue
        mark = b.mark()
        try:
            _clause(left, b)
        except (NoMatch, Incomplete):
            b.rewind(mark)
            continue
        try:
            _sequence(right, b)
            return
        except Incomplete as e:                 # left was fine, right needs a detail: remember the question
            b.rewind(mark)
            pending = pending or e
        except NoMatch:
            b.rewind(mark)
    try:
        _clause(text, b)
    except NoMatch:
        if pending:
            raise pending
        raise


def parse(text: str) -> dict | None:
    """-> {"intent":"command","steps":[...]} | {"intent":"clarify","question"} | {"intent":"refuse","message"} | None
    None means "this is not a command" (the router then tries the other intents and finally chat)."""
    b = Builder()
    try:
        _sequence(normalize_spoken(text), b)
    except Incomplete as e:
        return {"intent": "clarify", "question": e.question}
    except Refuse as e:
        return {"intent": "refuse", "message": e.message}
    except NoMatch:
        return None
    return {"intent": "command", "steps": b.steps}


def looks_like_command(text: str) -> bool:
    """Starts with an unmistakable device verb but no rule matched: answer with help, do not guess with a model."""
    return bool(_COMMAND_VERB.match(clean(text)))


def parse_mixed(text: str):
    """A sentence that is part COMMAND, part something else (e.g. an RAG query or browser question):
         "open project in vscode and search Java Stream API"      -> command first, then answer
         "ask about Java streams and open project in vscode"      -> answer first, then command
    -> (plan, remainder_text, order)  with order "command_first" | "question_first", or None.
    The command part must parse COMPLETELY; the other part must not look like a command (so a half-understood command
    never silently becomes a chat or search question)."""
    text = normalize_spoken(text)
    for m in _CONJ.finditer(text):
        left, right = text[:m.start()].strip(), text[m.end():].strip()
        if not left or not right:
            continue
        pl, pr = parse(left), parse(right)
        if pl and pl["intent"] == "command" and pr is None and len(right.split()) >= 2 and not looks_like_command(right):
            return pl, right, "command_first"
        if pr and pr["intent"] == "command" and pl is None and len(left.split()) >= 2 and not looks_like_command(left):
            return pr, left, "question_first"
    return None
