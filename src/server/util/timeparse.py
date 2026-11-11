"""Human time parsing done in CODE (small models are unreliable at dates/arithmetic)."""
import re
from datetime import datetime, timedelta

_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
          "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60}
_UNIT = {"s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
         "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
         "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600}
_NUM = r"(\d+(?:\.\d+)?|" + "|".join(sorted(_WORDS, key=len, reverse=True)) + r")"
_DUR = re.compile(_NUM + r"\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?|s|m|h)\b")


def parse_duration(text: str) -> int:
    """'10 minutes' / '1 hour 30 minutes' / 'half an hour' / 'an hour and a half' -> seconds."""
    t = text.lower().replace("-", " ")
    t = re.sub(r"\b(twenty|thirty|forty|fifty)\s+(one|two|three|four|five|six|seven|eight|nine)\b",
               lambda m: str(_WORDS[m.group(1)] + _WORDS[m.group(2)]), t)
    total = 0.0
    if re.search(r"half an? hour", t):
        total += 1800
        t = re.sub(r"half an? hour", " ", t)
    elif re.search(r"(an?|one|\d+)\s*hours?\s*(and )?a half", t):
        total += 1800
    found = total > 0
    for num, unit in _DUR.findall(t):
        n = float(num) if num[0].isdigit() else _WORDS[num]
        total += n * _UNIT[unit]
        found = True
    if not found or total <= 0:
        raise ValueError(f"Could not understand duration '{text}'")
    return int(total)


def fmt_duration(secs: float) -> str:
    secs = int(round(secs))
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m" if m else f"{h}h"
    if m:
        return f"{m}m {s:02d}s" if s and m < 5 else f"{m}m"
    return f"{s}s"


_DAYPART_TIME = {"morning": "9am", "afternoon": "3pm", "evening": "6pm", "night": "9pm"}


def _normalize_when(t: str) -> str:
    """dateparser does not know 'tomorrow morning', 'tonight' or 'next monday 9am'; spell them out."""
    t = t.lower().strip()
    t = re.sub(r"\btonight\b", "today at 9pm", t)
    t = re.sub(r"\bthis (morning|afternoon|evening)\b", lambda m: "today at " + _DAYPART_TIME[m.group(1)], t)
    t = re.sub(r"\b(today|tomorrow)\s+(morning|afternoon|evening|night)\b",
               lambda m: f"{m.group(1)} at {_DAYPART_TIME[m.group(2)]}", t)
    t = re.sub(r"\bnext\s+(?=(?:mon|tue|wed|thu|fri|sat|sun))", "", t)       # "next monday" = the coming monday
    t = re.sub(r"^(?:on|at)\s+", "", t)
    return t


def parse_when(text: str, now: datetime | None = None) -> datetime:
    """'in 2 hours' / 'tomorrow at 5pm' / '5pm' / 'next monday 9am' -> datetime (always in the future)."""
    now = now or datetime.now()
    t = text.strip()
    if re.match(r"^(in|after)\s", t.lower()):
        return now + timedelta(seconds=parse_duration(t))
    try:
        import dateparser
    except ImportError:
        raise ValueError("Install 'dateparser' to use clock times (pip install dateparser)")
    dt = dateparser.parse(_normalize_when(t), settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": now})
    if dt is None:
        raise ValueError(f"Could not understand the time '{text}'")
    if dt <= now and (now - dt) < timedelta(days=1) and not re.search(r"yesterday|ago|last|\d{4}", t.lower()):
        dt += timedelta(days=1)                      # "5pm" said at 6pm means tomorrow
    if dt <= now:
        raise ValueError(f"'{text}' is in the past")
    return dt


def parse_range(text: str, now: datetime | None = None):
    """Free text -> (start, end, label). Default = today so far."""
    now = now or datetime.now()
    q = text.lower()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    m = re.search(r"(?:last|past)\s+(\d+|an?|one|two|three|four|five|six)?\s*(hour|hr|minute|min)s?", q)
    if m:
        n = m.group(1)
        n = 1 if not n else (int(n) if n.isdigit() else _WORDS[n])
        delta = timedelta(hours=n) if m.group(2) in ("hour", "hr") else timedelta(minutes=n)
        return now - delta, now, f"the last {n} {m.group(2)}{'s' if n != 1 else ''}"
    if "last week" in q:
        start = midnight - timedelta(days=midnight.weekday() + 7)
        return start, start + timedelta(days=7), "last week"
    if "this week" in q:
        return midnight - timedelta(days=midnight.weekday()), now, "this week"
    day, label = midnight, "today"
    end_of_day = (midnight + timedelta(days=1)) if "yesterday" not in q else midnight
    if "yesterday" in q:
        day, label = midnight - timedelta(days=1), "yesterday"
        end_of_day = midnight
    else:
        end_of_day = now
    if "before lunch" in q:
        return day, day.replace(hour=13), f"{label} before lunch"
    if "after lunch" in q:
        return day.replace(hour=13), end_of_day, f"{label} after lunch"
    if "morning" in q:
        return day.replace(hour=5), min(day.replace(hour=12), end_of_day), f"{label} morning"
    if "afternoon" in q:
        return day.replace(hour=12), min(day.replace(hour=18), end_of_day), f"{label} afternoon"
    if "evening" in q:
        return day.replace(hour=18), end_of_day, f"{label} evening"
    return day, end_of_day, label


# ---------------------------------------------------------------------------------------------
# Phrase locators for the deterministic command grammar (no LLM): find the time expression inside a sentence.
# ---------------------------------------------------------------------------------------------
_DAYS = r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tues?|wed|thu(?:rs?)?|fri|sat|sun)"
_MONTHS = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
_CLOCK = r"(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)|\d{1,2}:\d{2}|noon|midnight)"
_NUMW = "|".join(sorted(_WORDS, key=len, reverse=True))
_IN = rf"in\s+(?:half an hour|(?:(?:\d+(?:\.\d+)?|{_NUMW})\s*(?:seconds?|secs?|minutes?|mins?|hours?|hrs?)\s*(?:and\s+)?)+)"
_DAYPART = r"(?:tomorrow|today|tonight|this\s+(?:morning|afternoon|evening)|tomorrow\s+(?:morning|afternoon|evening|night))"
_DATE = rf"(?:on\s+)?(?:\d{{1,2}}(?:st|nd|rd|th)?\s+{_MONTHS}|{_MONTHS}\s+\d{{1,2}}(?:st|nd|rd|th)?)"
WHEN = (rf"(?:{_IN.rstrip()}|(?:{_DAYPART}|(?:(?:next|this|on)\s+)?{_DAYS}|{_DATE})(?:\s+(?:at\s+)?{_CLOCK})?"
        rf"|(?:at\s+)?{_CLOCK})")
_REPEAT = re.compile(rf"\b(?:every\s+(?P<unit>day|morning|evening|night|week)|(?P<adv>daily|weekly)"
                     rf"|every\s+(?P<dow>{_DAYS}))\b", re.I)
_TRAIL = re.compile(rf"^(?P<body>.+?)\s+(?P<when>{WHEN})\s*$", re.I)
_LEAD = re.compile(rf"^(?P<when>{WHEN})\s+(?:to\s+|that\s+|about\s+)?(?P<body>.+)$", re.I)

# a period of the day(s) for activity queries
PERIOD = (r"(?:today|yesterday|this week|last week|(?:the\s+)?(?:last|past)\s+(?:\d+|an?|one|two|three|four|five|six)?\s*"
          r"(?:hours?|hrs?|minutes?|mins?)|this morning|this afternoon|this evening|before lunch|after lunch)")


def split_when(text: str):
    """'submit the assignment tomorrow at 5pm' -> ('submit the assignment', 'tomorrow at 5pm', '').
    'log my hours every day at 9am' -> ('log my hours', '9am', 'daily'). Raises ValueError if no time is found."""
    text, repeat = text.strip(), ""
    m = _REPEAT.search(text)
    if m:
        if m.group("dow"):
            repeat, dow = "weekly", m.group("dow")
            text = (text[:m.start()] + f" on {dow} " + text[m.end():]).strip()
        else:
            repeat = "weekly" if (m.group("unit") == "week" or m.group("adv") == "weekly") else "daily"
            text = (text[:m.start()] + " " + text[m.end():]).strip()
        text = re.sub(r"\s+", " ", text)
    for rx in (_TRAIL, _LEAD):
        m = rx.match(text)
        if m and m.group("body").strip():
            return m.group("body").strip(" ,"), m.group("when").strip(), repeat
    raise ValueError("no time found")
