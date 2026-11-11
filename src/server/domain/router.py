"""Intent router: text -> Route, with NO model call.

Order of evaluation:
    1. RAG query: Explicit 'ask', '/ask', 'search', '/search' queries routed to RAG with SQLite memory.
    2. Deterministic command engine: Executed strictly in code with zero LLM guesswork.
    3. Default browser fallback: Queries not matching commands or RAG are searched in the default browser.
"""
import re
from dataclasses import dataclass, field

from server import commands
from server.util.text import normalize_spoken

RAG_PREFIX = re.compile(r"^/?(?:ask|search)\b(?:\s+(?:me|for|in|about|through|from))?\s*[:,\-]?\s*", re.I)
RAG_BARE = re.compile(r"^/?(?:ask|search)\b\s*$", re.I)


def is_rag_query(text: str) -> tuple[bool, str]:
    """Identify if the query initiates an RAG knowledge search.

    Matches queries beginning with 'ask', '/ask', 'search', or '/search', handling
    common voice prepositions ('ask about...', 'search for...', etc.).
    Returns (True, extracted_question) if matched, or (False, "") otherwise.
    """
    clean_text = text.strip()
    if RAG_BARE.match(clean_text):
        return True, ""
    m = RAG_PREFIX.match(clean_text)
    if m:
        question = clean_text[m.end():].strip()
        return True, question
    return False, ""


SCREEN = re.compile(
    r"\b(?:what(?:'s| is)\s+(?:this|that|on)\s+(?:error|my screen|the screen)|what(?:'s| is)\s+wrong\s+(?:here|with this)|"
    r"(?:look at|check|read|explain|help (?:me )?with)\s+(?:my|this|the)\s+(?:screen|error)|"
    r"why (?:is|am)\s+(?:this|it)\s+(?:failing|not working|showing|giving)|what does this error (?:mean|say)|"
    r"(?:fix|debug)\s+(?:this|the)\s+error|screen help)\b", re.I)
SUMMARY = re.compile(r"(?:summari[sz]e|recap)\s+(?:my\s+|the\s+)?(?:day|today|yesterday)"
                     r"|(?:give me |show me )?(?:my |the )?(?:daily|day)\s+(?:summary|recap)(?:\s+for\s+(?:today|yesterday))?", re.I)
ACTIVITY = re.compile(
    r"\bwhat (?:was|were|am) i (?:doing|working on|up to)\b|\bwhat did i (?:do|work on|spend)\b(?! wrong)|"
    r"\bhow (?:much|long)\b.*\b(?:i|my)\b.*\b(?:spent|spend|worked|used)\b|"
    r"\bwhich (?:apps?|websites?|sites?) (?:did|have) i\b|\bwhat (?:apps?|websites?) (?:did|have) i\b|"
    r"\bwhen did i (?:start|stop|last|first)\b.*\b(?:work|code|coding|using|use)\b", re.I)
DOCS = re.compile(
    r"^(?:according to|based on|from|in|using)\s+(?:my|the)\s+(?:documents?|docs|files|pdfs?|notes files)\b|"
    r"\b(?:what|which)\b.*\b(?:do|does|did)\s+(?:my|the)\s+(?:documents?|docs|files|pdfs?|notes files|assignments?)\s+"
    r"(?:say|mention|contain|state|explain)\b|"
    r"\b(?:search|look)\s+(?:in |through )?my\s+(?:documents?|docs|files|pdfs?)\b", re.I)


SMALLTALK = [
    (re.compile(r"(?:hi|hello|hey|hii+|good (?:morning|afternoon|evening))(?:\s+(?:there|assistant))?", re.I),
     "Hello! Ask me a question about the Ignite programme or technical topics, or give me a command. Say 'help' to see what I can do."),
    (re.compile(r"(?:thanks|thank you|thx|ty)(?:\s+(?:a lot|so much))?", re.I), "You're welcome!"),
    (re.compile(r"(?:bye|goodbye|see you|good night)", re.I), "Goodbye!"),
    (re.compile(r"(?:who are you|what are you)", re.I),
     "I'm your trainee assistant: I run commands on your computer and answer questions from the Ignite and General knowledge bases."),
]


@dataclass
class Route:
    kind: str                       # command | clarify | refuse | screen | summary | activity | docs | rag | browser
    plan: dict | None = None
    message: str = ""
    extra: dict = field(default_factory=dict)


def route(text: str, allow_mixed: bool = True) -> Route:
    """Determine the processing route for incoming user input.

    1. Checks for explicit RAG search prefixes ("ask", "/ask", "search", "/search").
    2. Checks for deterministic commands and mixed command sequences.
    3. Falls back to writing the query directly into the default web browser.
    """
    t = normalize_spoken(text.strip())

    # 1. RAG query prefixes
    is_rag, rag_q = is_rag_query(t)
    if is_rag:
        if not rag_q:
            return Route("clarify", message="What would you like me to search or ask?")
        return Route("rag", extra={"question": rag_q, "raw": t})

    # 2. Deterministic command grammar
    plan = commands.parse(t)
    if plan:
        if plan["intent"] == "command":
            return Route("command", plan=plan)
        if plan["intent"] == "clarify":
            return Route("clarify", message=plan["question"])
        return Route("refuse", message=plan["message"])

    # Command chaining / mixed instructions (e.g. command + RAG query)
    if allow_mixed:
        mixed = commands.parse_mixed(t)
        if mixed:
            cmd_plan, rest, order = mixed
            return Route("mixed", plan=cmd_plan, extra={"remainder": rest, "order": order})

    # Deterministic features
    if SCREEN.search(t):
        return Route("screen", extra={"question": t})
    if SUMMARY.fullmatch(t.rstrip(".!? ")):
        return Route("summary", extra={"day": "yesterday" if "yesterday" in t.lower() else "today"})
    if ACTIVITY.search(t):
        return Route("activity", extra={"question": t})
    if DOCS.search(t):
        return Route("rag", extra={"question": t})
    for rx, reply in SMALLTALK:
        if rx.fullmatch(t.rstrip(".!? ")):
            return Route("smalltalk", message=reply)
    if commands.looks_like_command(t):
        return Route("clarify", message="I didn't understand that command. Say 'help' to see what I can do.")

    # 3. Default fallback: Unrecognized queries are launched in the default browser
    return Route("browser", extra={"query": t})
