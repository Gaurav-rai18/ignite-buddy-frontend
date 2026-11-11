"""
Daily summary (map-reduce). Numbers come from sessionize (code). The LLM only writes prose:
  MAP    : Qwen 2.5 (fast) describes each long session in 1-2 sentences from facts only
  REDUCE : Qwen 3.5 writes highlights / blockers from those descriptions, streamed
Summaries and session descriptions are embedded (nomic) so activity chat can search past days.
"""
import json
import time
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

import numpy as np

from server import config, llm
from server.util.timeparse import fmt_duration as fmt
from . import sessionize
from .sessionize import hhmm

MIN_SESSION = 300      # sessions shorter than 5 min are only counted, not described
MAX_SESSIONS = 10
CACHE_SECONDS = 600

MAP_SYSTEM = ("You summarize one block of computer activity. Use ONLY the facts given. Write 1-2 plain "
              "sentences about what the person was most likely doing. Do not invent file contents or details "
              "you cannot see. Do not mention exact durations.")
REDUCE_SYSTEM = ("You write a short end-of-day recap for a trainee from the facts given. Use ONLY the facts. "
                 "Output exactly two sections:\nWhat you worked on: 2-4 bullet points.\n"
                 "Possible blockers or unfinished items: 0-3 bullet points, or 'None visible.'\n"
                 "Do not state durations or percentages (they are shown separately). Be concise and encouraging.")


def day_bounds(day: date, now: datetime | None = None):
    now = now or datetime.now()
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    if day == now.date():
        end = now
    return start, end


def load_events(store, start_ts: float, end_ts: float) -> list[dict]:
    with store.conn() as con:
        rows = con.execute(
            "SELECT start_ts,end_ts,app,title,idle FROM activity_events "
            "WHERE end_ts>? AND start_ts<? ORDER BY start_ts", (start_ts, end_ts)).fetchall()
    return [{"start": max(r[0], start_ts), "end": min(r[1], end_ts), "app": r[2], "title": r[3], "idle": r[4]}
            for r in rows]


def has_activity(store, day: date) -> bool:
    s, e = day_bounds(day)
    return any(not x["idle"] for x in load_events(store, s.timestamp(), e.timestamp()))


_DESCRIPTIVE = {"find_folder", "find_file", "run_file", "open_app", "open_url", "web_search", "open_in_app"}


def actions_between(store, start_ts: float, end_ts: float) -> list[tuple[float, str]]:
    with store.conn() as con:
        rows = con.execute(
            "SELECT ts, tool, args FROM actions WHERE status='ok' AND ts BETWEEN ? AND ? ORDER BY ts",
            (start_ts, end_ts)).fetchall()
    out = []
    for ts, tool, args in rows:
        label = tool
        if tool in _DESCRIPTIVE:
            try:
                first = str(next(iter(json.loads(args).values())))
                if tool == "open_url":
                    first = urlparse(first if "://" in first else "https://" + first).netloc
                label = f"{tool}({first[:40]})"
            except Exception:
                pass
        out.append((ts, label))
    return out


def session_facts(s: dict, actions=()) -> str:
    apps = ", ".join(f"{a} {fmt(sec)}" for a, sec in s["apps"].most_common(4))
    titles = "; ".join(f"'{t[:70]}' ({fmt(sec)})" for t, sec in s["titles"].most_common(4))
    acts = [a for ts, a in actions if s["start"] <= ts <= s["end"]]
    text = f"{hhmm(s['start'])}-{hhmm(s['end'])}, active {fmt(s['active'])}. Apps: {apps}. " \
           f"Window titles: {titles or 'none'}."
    return text + (f" Assistant commands: {', '.join(acts[:6])}." if acts else "")


def _fallback(s: dict) -> str:
    app, secs = s["apps"].most_common(1)[0]
    return f"Mostly working in {app}."


def describe_sessions(sessions, actions, progress=lambda m: None):
    big = sorted([s for s in sessions if s["active"] >= MIN_SESSION], key=lambda s: -s["active"])[:MAX_SESSIONS]
    big.sort(key=lambda s: s["start"])
    out = []
    for i, s in enumerate(big, 1):
        progress(f"Summarizing session {i}/{len(big)}...")
        try:
            text = llm.chat_text([{"role": "system", "content": MAP_SYSTEM},
                                  {"role": "user", "content": session_facts(s, actions)}],
                                 model=config.FAST_MODEL, temperature=0.2)
        except Exception:
            text = _fallback(s)
        out.append((s, text or _fallback(s)))
    return out


# ---------- storage ----------
def get_summary(store, day: date):
    with store.conn() as con:
        return con.execute("SELECT text, created FROM summaries WHERE day=? AND kind='day'",
                           (day.isoformat(),)).fetchone()


def save_summary(store, day: date, start: datetime, end: datetime, full_text: str, described):
    items = [("day", full_text, start.timestamp(), end.timestamp())]
    items += [("session", f"{hhmm(s['start'])}-{hhmm(s['end'])}: {d}", s["start"], s["end"]) for s, d in described]
    with store.conn() as con:
        con.execute("DELETE FROM summaries WHERE day=?", (day.isoformat(),))
        con.executemany("INSERT INTO summaries(day,kind,start_ts,end_ts,text,created) VALUES (?,?,?,?,?,?)",
                        [(day.isoformat(), k, s, e, t, time.time()) for (k, t, s, e) in items])
    try:                                                    # vectors for "when did I ..." search live in ChromaDB
        from server.knowledge.personal import PersonalVectors
        PersonalVectors().put_summaries(store.key, day.isoformat(), [(k, t) for k, t, _, _ in items])
    except Exception:
        pass                                                # embeddings down: the summary is still saved and readable


def search_summaries(store, question: str, k: int = 3):
    """Search historical daily and session summaries using vector embeddings."""
    try:
        from server.knowledge.personal import PersonalVectors
        return PersonalVectors().search_summaries(store.key, question, k)
    except Exception:
        return []


# ---------- main entry ----------
def stream_day_summary(store, day: date, progress=lambda m: None, force: bool = False, now: datetime | None = None):
    start, end = day_bounds(day, now)
    cached = get_summary(store, day)
    if cached and not force and time.time() - cached[1] < CACHE_SECONDS:
        yield cached[0]
        return
    events = load_events(store, start.timestamp(), end.timestamp())
    if not any(not e["idle"] for e in events):
        yield f"No activity was recorded for {day:%a %d %b}. (Tracking may have been paused.)"
        return
    sessions, stats = sessionize.analyze(events)
    header = sessionize.format_stats(f"Daily summary for {day:%a %d %b}", stats)
    yield header + "\n\n"                                   # instant, computed in code

    actions = actions_between(store, start.timestamp(), end.timestamp())
    described = describe_sessions(sessions, actions, progress)
    lines = [f"{hhmm(s['start'])}-{hhmm(s['end'])}: {d}" for s, d in described]
    other = sum(s["active"] for s in sessions) - sum(s["active"] for s, _ in described)
    if other > 60:
        lines.append(f"Plus shorter activities totalling about {fmt(other)}.")
    user = (f"Date: {day:%A %d %B}. Focus share: {stats['focus_pct']:.0f}%.\nSessions:\n" + "\n".join(lines))
    parts = []
    try:
        for chunk in llm.chat_stream([{"role": "system", "content": REDUCE_SYSTEM},
                                      {"role": "user", "content": user}]):
            if chunk:
                parts.append(chunk)
                yield chunk
    except GeneratorExit:
        raise
    except Exception as e:
        yield f"(Could not write the narrative: {e})"
        return
    save_summary(store, day, start, end, header + "\n\n" + "".join(parts), described)


def generate_day_summary_text(store, day: date) -> str:
    return "".join(stream_day_summary(store, day, force=True))
