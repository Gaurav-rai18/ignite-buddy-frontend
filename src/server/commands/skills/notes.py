"""Notes: one markdown file per note in a dedicated folder ON THE TRAINEE'S PC (Documents/TraineeAssistant/Notes).
Create / read / update / append / search / delete; delete asks on the PC and moves to Notes/.trash (recoverable).
Nothing about note contents is stored on the server."""
from shared import protocol as P
from ..model import CONFIRM, Incomplete, NoMatch, SAFE
from ..parser import rule
from ..registry import device_tool

device_tool(P.ADD_NOTE, SAFE, "Save a note as a file on the PC.", {"text": "str"})
device_tool(P.LIST_NOTES, SAFE, "List the most recent notes.", {})
device_tool(P.SEARCH_NOTES, SAFE, "Search notes by words.", {"query": "str"})
device_tool(P.READ_NOTE, SAFE, "Show one note.", {"query": "str"})
device_tool(P.APPEND_NOTE, SAFE, "Add a line to an existing note.", {"query": "str", "text": "str"})
device_tool(P.UPDATE_NOTE, SAFE, "Replace the text of a note.", {"query": "str", "text": "str"})
device_tool(P.DELETE_NOTE, CONFIRM, "Delete a note (moved to .trash; the PC asks first).", {"query": "str"})
device_tool(P.OPEN_NOTES, SAFE, "Open the notes folder.", {})

_FILLER = {"my", "the", "a", "an", "that", "this"}


def _q(q: str) -> str:
    q = q.strip()
    if not q or q.lower() in _FILLER:
        raise NoMatch
    return q


@rule(r"(?:take|make|add|write|save|jot)(?:\s+down)?(?:\s+(?:a|an))?\s+note(?:\s+that|\s+to self)?\s*[:,\-]?\s*(?P<text>.+)",
      examples=("take a note buy milk",))
def note_add_verb(m, b):
    b.add(P.ADD_NOTE, text=m.group("text").strip())


@rule(r"note(?:\s+down)?(?:\s*[:,\-]\s*|\s+that\s+)(?P<text>.+)", examples=("note: viva is on Friday", "note that the lab is closed"))
def note_add_short(m, b):
    b.add(P.ADD_NOTE, text=m.group("text").strip())


@rule(r"(?:remember|don't forget|dont forget)\s+that\s+(?P<text>.+)")
def note_remember(m, b):
    b.add(P.ADD_NOTE, text=m.group("text").strip())


@rule(r"open(?:\s+(?:my|the))?\s+notes(?:\s+(?:folder|directory))?|where\s+are\s+my\s+notes", examples=("open my notes folder",))
def notes_folder(m, b):
    b.add(P.OPEN_NOTES)


@rule(r"(?:list|show|display|what are)(?:\s+me)?(?:\s+all)?(?:\s+(?:my|the))?(?:\s+(?:recent|latest))?\s+notes",
      examples=("show my notes",))
def notes_list(m, b):
    b.add(P.LIST_NOTES)


@rule(r"what (?:did|do) i (?:note|write down|jot down|save)(?: down)?\s+(?:about|on|regarding)\s+(?P<q>.+)"
      r"|what (?:do|does|did) my notes (?:say|mention|have)\s+(?:about|on|regarding)\s+(?P<q2>.+)"
      r"|(?:search|find|look up|look through|check)(?:\s+in)?\s+my notes\s+(?:for|about|on)\s+(?P<q3>.+)"
      r"|(?:find|show)(?:\s+me)?\s+(?:my\s+)?notes?\s+(?:about|on|regarding)\s+(?P<q4>.+)",
      examples=("what did I note about the viva", "search my notes for deadline"))
def notes_search(m, b):
    b.add(P.SEARCH_NOTES, query=(m.group("q") or m.group("q2") or m.group("q3") or m.group("q4")).strip())


@rule(r"(?:read|show|open|display)(?:\s+me)?(?:\s+(?:my|the))?\s+note\s+(?:about|on|called|named|with)?\s*(?P<q>.+)"
      r"|(?:read|show|open|display)(?:\s+me)?(?:\s+(?:my|the))?\s+(?P<q2>.+?)\s+note",
      examples=("read the viva note",))
def note_read(m, b):
    b.add(P.READ_NOTE, query=_q(m.group("q") or m.group("q2")))


@rule(r"(?:add|append)(?:\s+this)?\s+to(?:\s+(?:my|the))?\s+(?P<q>.+?)\s+note\s*[:,\-]?\s*(?P<t>.+)"
      r"|append\s+(?P<t2>.+?)\s+to(?:\s+(?:my|the))?\s+(?P<q2>.+?)\s+note",
      examples=("add to my viva note: bring your ID",))
def note_append(m, b):
    b.add(P.APPEND_NOTE, query=_q(m.group("q") or m.group("q2")), text=(m.group("t") or m.group("t2")).strip())


@rule(r"(?:update|change|edit|rewrite)(?:\s+(?:my|the))?\s+(?P<q>.+?)\s+note\s+(?:to say|to read|to|with|:)\s*(?P<t>.+)",
      examples=("update the viva note to say moved to Monday",))
def note_update(m, b):
    b.add(P.UPDATE_NOTE, query=_q(m.group("q")), text=m.group("t").strip())


@rule(r"(?:delete|remove|erase)(?:\s+(?:my|the))?\s+note(?:\s+(?:about|on|regarding|with|called))?\s+(?P<q>.+)",
      examples=("delete the note about the viva",))
def note_delete(m, b):
    b.add(P.DELETE_NOTE, query=_q(m.group("q")))


@rule(r"(?:delete|remove|erase)(?:\s+(?:my|the))?\s+(?P<q>.+?)\s+note", examples=("delete the viva note",))
def note_delete_named(m, b):
    b.add(P.DELETE_NOTE, query=_q(m.group("q")))
