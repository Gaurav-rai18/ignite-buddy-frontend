"""Activity chat: 'what was I doing before lunch?', 'how long did I use VS Code today?'
Facts come from SQL + code (exact), past days from vector search over saved summaries, then the chat model answers."""
from datetime import datetime

from server import llm
from server.util import timeparse
from . import sessionize, summarize

SYSTEM = ("You answer questions about the user's OWN computer activity using ONLY the context. Copy numbers "
          "and times exactly from the context. If the context does not contain the answer, say you have no "
          "record of it. Be concise. Never guess what was inside files or pages beyond the window titles.")


def build_context(store, question: str, now: datetime | None = None) -> str:
    start, end, label = timeparse.parse_range(question, now)
    parts = [f"Period: {label} ({start:%a %d %b %H:%M} to {end:%a %d %b %H:%M})"]
    events = summarize.load_events(store, start.timestamp(), end.timestamp())
    if any(not e["idle"] for e in events):
        sessions, stats = sessionize.analyze(events)
        parts.append(sessionize.format_stats("Statistics for the period:", stats))
        actions = summarize.actions_between(store, start.timestamp(), end.timestamp())
        parts.append("Sessions:\n" + "\n".join("- " + summarize.session_facts(s, actions) for s in sessions[:15]))
    else:
        parts.append("No activity was recorded in this period.")
    past = summarize.search_summaries(store, question, 3)
    if past:
        parts.append("Saved summaries that may be relevant:\n" +
                     "\n".join(f"[{day}] {text[:600]}" for day, kind, text in past))
    return "\n\n".join(parts)


def answer(store, question: str, now: datetime | None = None):
    ctx = build_context(store, question, now)
    yield from llm.chat_stream([{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": f"Context:\n{ctx}\n\nQuestion: {question}"}])
