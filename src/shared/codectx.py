"""Pure helpers for the code helper ("what's this error?"): which file is open, and which line failed.
The server uses them to build the request; the client uses them to find and read the file locally."""
import re

_FILE_EXT = "py|js|ts|tsx|jsx|java|cs|cpp|c|h|html|css|json|bat|cmd|sh|md|sql|go|rb|php|yml|yaml|xml|txt|ipynb"
_FILE_RE = re.compile(rf"([\w\-. ]*?[\w\-]\.(?:{_FILE_EXT}))\b", re.I)
SENSITIVE_FILE = re.compile(r"(^\.env|\.env$|id_rsa|\.pem$|\.key$|\.pfx$|\.p12$|credential|secret|password|\.kdbx$)", re.I)


def filename_from_title(title: str):
    m = _FILE_RE.search(re.sub(r"^[\u25cf*\u2022\s]+", "", title or ""))
    return m.group(1).strip() if m else None


def error_line_for(name: str, text: str):
    m = re.search(rf"{re.escape(name)}[\"']?\s*[:,]?\s*(?:line\s*)?(\d+)", text or "", re.I)
    return int(m.group(1)) if m else None
