"""
One request = one call to process(session, text). No transport code, no model deciding what to do.

    route (rules) -> deterministic command  |  screen help  |  summary  |  activity Q&A  |  docs Q&A  |  chat (+RAG)
"""
import logging
from datetime import date, timedelta

from server import commands, llm
from server.chat import get_chat_service
from server.commands import PlanError
from server.features import screen_help
from server.features.activity import qa, summarize
from server.util.text import speakable
from shared import protocol as P
from . import router
from .session import Cancelled

log = logging.getLogger("orchestrator")
SPEAK_LIMIT = 300


def _stream(ui, chunks) -> str:
    ui.state("generating")
    parts = []
    for c in chunks:
        if c:
            parts.append(c)
            ui.token(c)
    ui.end_message()
    return "".join(parts)


def _remember(session, user_text, reply):
    session.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}]
    del session.history[:-40]


def _screen(session, question):
    ui = session.ui
    ui.state("thinking")
    cap = ui.capture_screen()
    if not cap:
        ui.say("Screen help cancelled.")
        return "Okay."
    reply = _stream(ui, screen_help.answer(session, question, cap, progress=ui.say))
    return speakable(reply, SPEAK_LIMIT)


def _summary(session, which):
    ui = session.ui
    day = date.today() - timedelta(days=1 if which == "yesterday" else 0)
    reply = _stream(ui, summarize.stream_day_summary(session.store, day, progress=ui.say))
    return speakable(reply, SPEAK_LIMIT)


def _index(session, folder):
    ui = session.ui
    ui.state("thinking")
    n = get_chat_service().personal_docs.index_folder(session, folder, say=ui.say)
    return f"Indexed {n} new chunks." if n else "Nothing new to index."


def _run_command(session, plan) -> bool:
    ui = session.ui
    try:
        plan = commands.validate(plan)
    except PlanError as e:
        log.warning("invalid plan from parser: %s", e)
        ui.say("I couldn't build a safe plan for that.")
        return False
    return commands.run_plan(session, plan["steps"])


def process(session, text: str):
    """Returns a short spoken reply (or None). Raises Cancelled if the user cancelled."""
    session.ui.state("thinking")
    try:
        return _dispatch(session, text.strip(), allow_mixed=True)
    except llm.LLMError as e:
        session.ui.say(str(e))
        return "I couldn't reach the model."


def _dispatch(session, low: str, allow_mixed: bool):
    ui = session.ui
    # ---- slash shortcuts (explicit, deterministic) ----
    if low.startswith("/screen"):
        return _screen(session, low[7:].strip() or screen_help.DEFAULT_QUESTION)
    if low.startswith("/summary"):
        return _summary(session, "yesterday" if "yesterday" in low else "today")
    if low.startswith("/index"):
        folder = low[6:].strip()
        return _index(session, folder) if folder else "Usage: /index <folder>"
    if low.startswith("/ask") or low.startswith("/search"):
        prefix_len = 4 if low.startswith("/ask") else 7
        q = low[prefix_len:].strip()
        if not q:
            ui.say("Please provide a question or search query.")
            return "Please provide a question to search."
        reply = _stream(ui, get_chat_service().stream_rag_answer(session, q))
        _remember(session, q, reply)
        return speakable(reply, SPEAK_LIMIT)

    r = router.route(low, allow_mixed)
    if r.kind == "command":
        return "Done." if _run_command(session, r.plan) else "Sorry, that didn't complete."
    if r.kind == "mixed":
        # "<command> and <question/rag>": each half is handled by its own engine; neither can swallow the other.
        rest = r.extra["remainder"]
        if r.extra["order"] == "command_first":
            ok = _run_command(session, r.plan)
            answer = _dispatch(session, rest, allow_mixed=False)
            return (answer if ok else f"The command didn't complete. {answer or ''}").strip()
        answer = _dispatch(session, rest, allow_mixed=False)
        ok = _run_command(session, r.plan)
        return f"{answer or ''} {'Done.' if ok else 'The command did not complete.'}".strip()
    if r.kind in ("clarify", "refuse", "smalltalk"):
        ui.say(r.message)
        return r.message
    if r.kind == "screen":
        return _screen(session, r.extra["question"])
    if r.kind == "summary":
        return _summary(session, r.extra["day"])
    if r.kind == "activity":
        return speakable(_stream(ui, qa.answer(session.store, r.extra["question"])), SPEAK_LIMIT)
    if r.kind == "rag":
        reply = _stream(ui, get_chat_service().stream_rag_answer(session, r.extra["question"]))
        _remember(session, r.extra["question"], reply)
        return speakable(reply, SPEAK_LIMIT)
    if r.kind == "browser":
        query = r.extra.get("query") or low
        ui.say(f"Searching web for '{query}'...")
        plan = {"intent": "command", "steps": [{"id": 1, "tool": P.WEB_SEARCH, "args": {"query": str(query)}}]}
        ok = _run_command(session, plan)
        return f"Searching for {query}." if ok else "Could not open browser."
    query = r.extra.get("question") or r.extra.get("query") or low
    reply = _stream(ui, get_chat_service().stream_reply(session, query))
    _remember(session, query, reply)
    return speakable(reply, SPEAK_LIMIT)
