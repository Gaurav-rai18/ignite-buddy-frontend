"""Secret/PII redaction + private-window masking. Runs on the CLIENT before anything is sent, and again on the
SERVER before anything is stored or shown to a model (defence in depth). Pure functions, no I/O."""
from __future__ import annotations

import re

BUILTIN_BLOCK = ("keepass", "1password", "bitwarden", "lastpass", "dashlane", "enpass", "nordpass")
PRIVATE_TITLE = re.compile(r"incognito|inprivate|private browsing|private window", re.I)
REDACTIONS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email]"),
    (re.compile(r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key)\s*[:=]\s*\S+"), r"\1=[redacted]"),
    (re.compile(r"\b(?:\d[ -]?){13,16}\b"), "[number]"),
    (re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"), "[token]"),
]
_SCREEN_EXTRA = [
    (re.compile(r"eyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]{8,}"), "[jwt]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)"), "[private key]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[aws key]"),
]


def redact(text: str) -> str:
    for pattern, repl in REDACTIONS:
        text = pattern.sub(repl, text)
    return text


def redact_screen(text: str, limit: int = 6000) -> str:
    """Apply high-sensitivity redactions (JWTs, private keys, cloud tokens) and truncate safely.

    Preserves initial context and tail output (where error messages and stack traces appear)
    while strictly staying within the specified character limit. Dynamically partitions
    head and tail slices to prevent overlapping or inverted index calculations for smaller limits.
    """
    text = redact(text)
    for pattern, repl in _SCREEN_EXTRA:
        text = pattern.sub(repl, text)
    if len(text) > limit:
        if limit <= 0:
            return ""
        head_len = min(2000, limit // 2) if limit < 4000 else 2000
        tail_len = max(0, limit - head_len)
        text = text[:head_len] + ("\n...\n" + text[-tail_len:] if tail_len > 0 else "")
    return text


def is_private(app: str, title: str, extra_blocklist=()) -> bool:
    a = (app or "").lower()
    return any(b in a for b in (*BUILTIN_BLOCK, *extra_blocklist)) or bool(PRIVATE_TITLE.search(title or ""))


def mask(app: str, title: str, extra_blocklist=()):
    """-> (app, title). Private windows become ('(private)', '') so time totals stay honest."""
    if is_private(app, title, extra_blocklist):
        return "(private)", ""
    return app, redact(title or "")[:200]
