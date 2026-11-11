"""Deterministic "how long did I use X?" (no model): pure SQL + arithmetic over the user's activity events."""
from . import categories, summarize
from server.util import timeparse


def usage(store, subject: str, when: str = "today"):
    """-> (label_of_period, seconds_matched, seconds_active_total, matched_what)
    `subject` may be an app ('vs code'), a category ('coding') or words from a window title ('youtube')."""
    start, end, label = timeparse.parse_range(when or "today")
    events = [e for e in summarize.load_events(store, start.timestamp(), end.timestamp())
              if not e["idle"] and e["app"] != "(private)"]
    q = (subject or "").lower().strip()
    needle = categories.APP_ALIASES.get(q, q)
    cat = q if q in categories.CATEGORIES else None
    total = matched = 0.0
    for e in events:
        d = e["end"] - e["start"]
        total += d
        app, title = e["app"].lower(), (e["title"] or "").lower()
        hit = (cat and categories.categorize(e["app"], e["title"]) == cat) or needle in app or q in title
        if hit:
            matched += d
    return label, matched, total
