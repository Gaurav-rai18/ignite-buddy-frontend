"""
Plain-code analysis of raw events: sessions, time per category/app, focus %, longest focus streak.
All numbers come from here, never from the LLM (small models are bad at arithmetic).
"""
from collections import Counter
from datetime import datetime

from server.util.timeparse import fmt_duration as fmt
from . import categories

GAP = 300            # >5 min between active events starts a new session
STREAK_GAP = 120     # focus streak survives distractions shorter than this


def hhmm(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M")


def analyze(events: list[dict]):
    evs = sorted(events, key=lambda e: e["start"])
    sessions, cur = [], None
    for e in evs:
        if e["idle"]:
            continue
        dur = e["end"] - e["start"]
        cat = categories.categorize(e["app"], e["title"])
        if cur is None or e["start"] - cur["end"] > GAP:
            cur = {"start": e["start"], "end": e["end"], "active": 0.0, "idle": 0.0,
                   "apps": Counter(), "titles": Counter(), "cats": Counter()}
            sessions.append(cur)
        cur["end"] = max(cur["end"], e["end"])
        cur["active"] += dur
        cur["apps"][e["app"]] += dur
        cur["cats"][cat] += dur
        if e["title"] and e["app"] != "(private)":
            cur["titles"][e["title"]] += dur

    idle_total = 0.0
    for e in evs:
        if e["idle"]:
            d = e["end"] - e["start"]
            idle_total += d
            for s in sessions:
                if s["start"] <= e["start"] and e["end"] <= s["end"]:
                    s["idle"] += d

    cats, apps = Counter(), Counter()
    for s in sessions:
        cats.update(s["cats"])
        apps.update(s["apps"])
    active = sum(s["active"] for s in sessions)

    switches, prev, best, c_start, c_end = 0, None, (0.0, 0.0, 0.0), None, None
    for e in (x for x in evs if not x["idle"]):
        if prev and e["app"] != prev["app"] and e["start"] - prev["end"] <= GAP:
            switches += 1
        prev = e
        if categories.categorize(e["app"], e["title"]) in categories.FOCUS:
            if c_start is not None and e["start"] - c_end <= STREAK_GAP:
                c_end = max(c_end, e["end"])
            else:
                c_start, c_end = e["start"], e["end"]
            if c_end - c_start > best[0]:
                best = (c_end - c_start, c_start, c_end)

    focus = sum(cats[c] for c in categories.FOCUS)
    stats = {
        "active": active, "idle": idle_total, "n_sessions": len(sessions),
        "first": sessions[0]["start"] if sessions else None,
        "last": sessions[-1]["end"] if sessions else None,
        "cats": cats, "apps": apps,
        "focus_pct": (focus / active * 100) if active else 0.0,
        "longest": best, "switches": switches,
        "switches_per_hour": (switches / (active / 3600)) if active >= 600 else 0.0,
    }
    return sessions, stats


def format_stats(title: str, st: dict) -> str:
    if not st["active"]:
        return f"{title}\nNo active time recorded."
    cats = ", ".join(f"{c.capitalize()} {fmt(s)} ({s / st['active'] * 100:.0f}%)" for c, s in st["cats"].most_common())
    apps = ", ".join(f"{a} {fmt(s)}" for a, s in st["apps"].most_common(5))
    d, a, b = st["longest"]
    return "\n".join([
        title,
        f"Active {fmt(st['active'])} · Idle {fmt(st['idle'])} · {hhmm(st['first'])} to {hhmm(st['last'])}",
        f"Focus {st['focus_pct']:.0f}% · Longest focus {fmt(d)} ({hhmm(a)}-{hhmm(b)}) · "
        f"{st['switches_per_hour']:.0f} app switches/hour",
        f"By category: {cats}",
        f"Top apps: {apps}",
    ])
