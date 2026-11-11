"""Decide which space(s) to search for a query, and in what order. Deterministic (no model).
A query that mentions Ignite-programme vocabulary searches "ignite" first; everything else "general" first. The
second space is the fallback, so a question is never missed just because the hint was wrong."""
import re

from server import config
from server.domain import policy
from .store import SPACES


def _hint_regex():
    return re.compile(r"\b(?:" + "|".join(re.escape(h) for h in config.KB_IGNITE_HINTS) + r")\b", re.I) if config.KB_IGNITE_HINTS else None


def order_for(query: str) -> list[str]:
    rx = _hint_regex()
    return ["ignite", "general"] if rx and rx.search(query) else ["general", "ignite"]


def allowed_spaces(query: str, user_id: str | None) -> list[str]:
    """Routing order filtered by the admin's per-account switches (kb.ignite / kb.general)."""
    return [s for s in order_for(query) if s in SPACES and policy.allows(f"kb.{s}", user_id)]
