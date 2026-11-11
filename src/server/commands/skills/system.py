"""
Computer actions. These tools run ON THE CLIENT (device tools): the server only declares their schema and builds the
plan; the client resolves names against its own file index, enforces its folder allowlist and shows its own
confirmation for scripts. Grammar below turns sentences into those steps.
"""
import re

from shared import protocol as P
from ..model import CONFIRM, Incomplete, NoMatch, SAFE
from ..parser import rule
from ..registry import device_tool

device_tool(P.FIND_FOLDER, SAFE, "Find a folder by fuzzy name. Returns path.", {"query": "str"})
device_tool(P.FIND_FILE, SAFE, "Find a file by fuzzy name. Returns path, parent, name.", {"query": "str"})
device_tool(P.OPEN_APP, SAFE, "Launch an installed application by name.", {"name": "str"})
device_tool(P.OPEN_IN_APP, SAFE, "Open a path in an editor app (vs code, notepad).", {"app": "str", "path": "str"})
device_tool(P.OPEN_FOLDER, SAFE, "Open a folder in the file manager.", {"path": "str"})
device_tool(P.OPEN_FILE, SAFE, "Open a document with its default program (not scripts).", {"path": "str"})
device_tool(P.OPEN_TARGET, SAFE, "Open whatever best matches: an app, then a folder, then a file.", {"query": "str"})
device_tool(P.OPEN_URL, SAFE, "Open an https URL in the default browser.", {"url": "str"})
device_tool(P.WEB_SEARCH, SAFE, "Search the web in the default browser.", {"query": "str"})
device_tool(P.RUN_FILE, CONFIRM, "Run a .bat/.cmd/.sh/.py file; the client asks the user to approve first.",
            {"file": "str", "cwd": "str"})

_EXT = r"[\w\-. ]+?\.[A-Za-z0-9]{1,5}"
_SCRIPT = r"[\w\-. ]+?\.(?:bat|cmd|sh|py|ps1)"
_EDITOR = r"(?:vs ?code|visual studio code|vscode|code|notepad)"
_THE = r"(?:(?:the|my|up)\s+)*"
_STRIP_KIND = re.compile(r"^(?:the\s+)?(?:folder|directory|project|file)\s+", re.I)


def _find(b, query, *, folder: bool | None = None):
    """Add a find step. folder=None -> guess from the name: has an extension => file, otherwise folder."""
    query = _STRIP_KIND.sub("", query.strip())
    is_file = bool(re.search(r"\.[A-Za-z0-9]{1,5}$", query)) if folder is None else not folder
    sid = b.add(P.FIND_FILE if is_file else P.FIND_FOLDER, query=query)
    if not is_file:
        b.last_folder = sid
    return sid


@rule(rf"open\s+{_THE}(?P<t>.+?)\s+(?:in|with|using)\s+(?P<app>{_EDITOR})",
      examples=("open the react assignment 3 in vs code",))
def open_in_editor(m, b):
    sid = _find(b, m.group("t"))
    b.add(P.OPEN_IN_APP, app=m.group("app"), path=b.ref(sid))


@rule(r"(?:open|go to|visit|browse to)\s+(?:the\s+|my\s+)?(?:website\s+|site\s+|page\s+|url\s+)?"
      r"(?P<u>https?://\S+|(?:www\.)?[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|io|dev|in|edu|gov|ai|co|app)(?:/\S*)?)",
      examples=("open github.com",))
def open_url(m, b):
    b.add(P.OPEN_URL, url=m.group("u"))


@rule(rf"open\s+{_THE}(?:folder|directory)\s+(?P<q>.+)|open\s+{_THE}(?P<q2>.+?)\s+(?:folder|directory)",
      examples=("open the react assignment 3 folder",))
def open_folder(m, b):
    sid = _find(b, m.group("q") or m.group("q2"), folder=True)
    b.add(P.OPEN_FOLDER, path=b.ref(sid))


@rule(rf"open\s+{_THE}(?:file\s+)?(?P<q>{_EXT})|open\s+{_THE}file\s+(?P<q2>.+)|open\s+{_THE}(?P<q3>.+?)\s+file",
      examples=("open resume.pdf",))
def open_file(m, b):
    sid = _find(b, m.group("q") or m.group("q2") or m.group("q3"), folder=False)
    b.add(P.OPEN_FILE, path=b.ref(sid))


@rule(rf"(?:launch|start|open)\s+{_THE}(?P<n>.+?)\s+(?:app|application|program)|launch\s+{_THE}(?P<n2>.+)",
      examples=("launch chrome",))
def open_app(m, b):
    b.add(P.OPEN_APP, name=(m.group("n") or m.group("n2")).strip())


@rule(rf"(?:run|execute)\s+{_THE}(?P<f>{_SCRIPT})(?:\s+(?:file|script))?(?:\s+(?:in|from|inside|under)\s+{_THE}(?:(?:folder|directory|project)\s+)?(?P<d>.+))?",
      examples=("run install.bat in react assignment 3",))
def run_script(m, b):
    f, d = m.group("f").strip(), m.group("d")
    if d:
        cwd = b.ref(_find(b, d, folder=True))
    elif b.last_folder:
        cwd = b.ref(b.last_folder)                      # "...open X in vs code and run install.bat"
    else:
        sid = b.add(P.FIND_FILE, query=f)               # no folder given: locate the script by name
        b.add(P.RUN_FILE, file=b.ref(sid, "name"), cwd=b.ref(sid, "parent"))
        return
    b.add(P.RUN_FILE, file=f, cwd=cwd)


@rule(r"(?:run|execute)\s+(?:the\s+|a\s+)?(?:file|script|batch file|it|that)")
def run_unspecified(m, b):
    raise Incomplete("Which file should I run, and in which folder? For example: 'run install.bat in react assignment 3'.")


@rule(r"(?:find|locate)(?:\s+me)?\s+{the}(?:(?P<k>folder|directory|file)\s+)?(?P<q>.+?)(?:\s+(?P<k2>folder|directory|file))?"
      .replace("{the}", _THE), examples=("find my resume.pdf",))
def find_path(m, b):
    q = m.group("q").strip()
    if len(q.split()) > 6 or re.match(r"(?:out|a |an |some |how|why|what)\b", q, re.I):
        raise NoMatch                                   # "find out how X works" is a question, not a file search
    kind = (m.group("k") or m.group("k2") or "").lower()
    _find(b, q, folder=True if kind in ("folder", "directory") else (False if kind == "file" else None))


@rule(r"open\s+(?P<q>.+)")
def open_best_match(m, b):
    """Last resort for 'open X': the client tries an app, then a folder, then a file."""
    q = m.group("q").strip()
    if len(q.split()) > 7 or re.search(r"\b(?:and|then)\s+(?:open|run|launch|remind|set|start|search|note|cancel|pause|resume|delete|show|list)\b", q, re.I):
        raise NoMatch
    b.add(P.OPEN_TARGET, query=_STRIP_KIND.sub("", re.sub(r"^(?:the|my)\s+", "", q, flags=re.I)))
