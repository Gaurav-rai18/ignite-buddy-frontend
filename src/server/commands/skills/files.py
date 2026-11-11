"""
File and folder CRUD (create / read / list / rename / move / copy / delete) on the trainee's PC.
Each tool is gated by an ADMIN capability (core/policy.py: files.create, files.read, files.copy, files.rename,
files.move, files.delete). Delete is OFF by default; when enabled it asks on the PC and uses the Recycle Bin.
The PC additionally confines everything to its allowed folders.
"""
import re

from shared import protocol as P
from ..model import CONFIRM, Incomplete, NoMatch, SAFE
from ..parser import rule
from ..registry import device_tool

device_tool(P.CREATE_FOLDER, SAFE, "Create a folder.", {"name": "str", "parent": "str?"}, capability="files.create")
device_tool(P.CREATE_FILE, SAFE, "Create a text/code file (never executables).",
            {"name": "str", "parent": "str?", "content": "str?"}, capability="files.create")
device_tool(P.RENAME_PATH, SAFE, "Rename a file or folder.", {"path": "str", "new_name": "str"}, capability="files.rename")
device_tool(P.MOVE_PATH, SAFE, "Move a file or folder into another folder.", {"path": "str", "destination": "str"},
            capability="files.move")
device_tool(P.COPY_PATH, SAFE, "Copy a file or folder into another folder.", {"path": "str", "destination": "str"},
            capability="files.copy")
device_tool(P.DELETE_PATH, CONFIRM, "Move a file/folder to the Recycle Bin (the PC asks first).", {"path": "str"},
            capability="files.delete")
device_tool(P.READ_FILE, SAFE, "Show the text of a file.", {"path": "str"}, capability="files.read")
device_tool(P.LIST_FOLDER, SAFE, "List what is inside a folder.", {"path": "str"}, capability="files.read")

_THE = r"(?:(?:the|my|a|an|new)\s+)*"
_KIND = re.compile(r"^(?:the\s+)?(?:folder|directory|project|file)\s+", re.I)
_PLACE = r"(?:in|inside|under|on|within|into)"


def _is_file(name: str) -> bool:
    return bool(re.search(r"\.[A-Za-z0-9]{1,5}$", name.strip()))


def _locate(b, name: str, *, folder: bool | None = None) -> str:
    """Add the find step for an existing file/folder and return a reference to its path."""
    name = _KIND.sub("", name.strip())
    is_file = _is_file(name) if folder is None else not folder
    sid = b.add(P.FIND_FILE if is_file else P.FIND_FOLDER, query=name)
    return b.ref(sid)


def _parent(b, parent):
    return _locate(b, parent, folder=True) if parent else None


@rule(rf"(?:create|make|add|new)\s+{_THE}(?:folder|directory)(?:\s+(?:called|named))?\s+(?P<name>.+?)"
      rf"(?:\s+{_PLACE}\s+(?:the\s+|my\s+)?(?:folder\s+)?(?P<parent>.+))?",
      examples=("create a folder called react notes in documents",))
def create_folder(m, b):
    parent = _parent(b, m.group("parent"))
    b.add(P.CREATE_FOLDER, name=m.group("name").strip(), parent=parent)


@rule(rf"(?:create|make|add|new)\s+{_THE}(?:empty\s+)?file(?:\s+(?:called|named))?\s+(?P<name>[\w\-. ]+?)"
      rf"(?:\s+{_PLACE}\s+(?:the\s+|my\s+)?(?:folder\s+)?(?P<parent>.+?))?"
      rf"(?:\s+(?:with|containing)\s+(?:the\s+)?(?:content\s+|text\s+)?(?P<content>.+))?",
      examples=("create a file todo.txt in desktop",))
def create_file(m, b):
    name = m.group("name").strip()
    parent = _parent(b, m.group("parent"))
    b.add(P.CREATE_FILE, name=name, parent=parent, content=(m.group("content") or "").strip() or None)


@rule(r"rename(?:\s+the)?(?:\s+(?:file|folder))?\s+(?P<src>.+?)\s+to\s+(?P<new>.+)", examples=("rename report.docx to final",))
def rename(m, b):
    path = _locate(b, m.group("src"))
    b.add(P.RENAME_PATH, path=path, new_name=m.group("new").strip())


@rule(r"move(?:\s+the)?(?:\s+(?:file|folder))?\s+(?P<src>.+?)\s+(?:to|into|in)\s+(?:the\s+)?(?:folder\s+)?(?P<dst>.+)",
      examples=("move report.docx to desktop",))
def move(m, b):
    path = _locate(b, m.group("src"))
    b.add(P.MOVE_PATH, path=path, destination=_locate(b, m.group("dst"), folder=True))


@rule(r"(?:copy|duplicate)(?:\s+the)?(?:\s+(?:file|folder))?\s+(?P<src>.+?)\s+(?:to|into|in)\s+(?:the\s+)?(?:folder\s+)?(?P<dst>.+)",
      examples=("copy report.docx to downloads",))
def copy(m, b):
    path = _locate(b, m.group("src"))
    b.add(P.COPY_PATH, path=path, destination=_locate(b, m.group("dst"), folder=True))


@rule(r"(?:delete|remove|trash)(?:\s+(?:the|my))?\s+(?:(?P<k>file|folder|directory)\s+)?(?P<q>.+?)(?:\s+(?P<k2>file|folder|directory))?",
      examples=("delete the file old-notes.txt",))
def delete(m, b):
    q, kind = m.group("q").strip(), (m.group("k") or m.group("k2") or "").lower()
    if not kind and not _is_file(q):
        raise NoMatch                                   # "delete the pasta timer" etc. belong to other skills
    b.add(P.DELETE_PATH, path=_locate(b, q, folder=True if kind in ("folder", "directory") else (False if kind == "file" else None)))


@rule(r"(?:read|show|display|cat|view)(?:\s+me)?(?:\s+(?:the|my))?(?:\s+(?:contents? of|what'?s in|what is in))?(?:\s+the)?(?:\s+file)?"
      r"\s+(?P<q>[\w\-. ]+?\.[A-Za-z0-9]{1,5})", examples=("read notes.txt",))
def read(m, b):
    b.add(P.READ_FILE, path=_locate(b, m.group("q"), folder=False))


@rule(r"(?:list|show)(?:\s+me)?(?:\s+(?:the|my|all))?(?:\s+(?:files|contents|items|everything))?\s+(?:in|inside|of)\s+(?:the\s+|my\s+)?(?:folder\s+)?(?P<q>.+)"
      r"|what'?s\s+in\s+(?:the\s+|my\s+)?(?:folder\s+)?(?P<q2>.+)|ls\s+(?P<q3>.+)",
      examples=("list files in downloads",))
def list_folder(m, b):
    q = m.group("q") or m.group("q2") or m.group("q3")
    b.add(P.LIST_FOLDER, path=_locate(b, q, folder=True))
