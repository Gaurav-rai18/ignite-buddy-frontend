"""Web browsing commands to open external search queries directly in the user's default browser."""
from shared import protocol as P
from ..parser import rule

_NOT_LOCAL = r"(?!(?:in |through |inside )?(?:my|the) (?:notes?|documents?|docs|files?|pdfs?|folders?)\b)"


@rule(rf"(?:search|google|look up|lookup|web search)(?:\s+(?:the web|online|the internet|google))?(?:\s+for)?\s+{_NOT_LOCAL}(?P<q>.+)",
      examples=("search django channels tutorial", "google python decorators"))
def search(m, b):
    """Dispatch an explicit web search action to launch Google in the user's default browser."""
    b.add(P.WEB_SEARCH, query=m.group("q").strip())
