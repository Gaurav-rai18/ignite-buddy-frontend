"""Plan validation. The parser should never produce an invalid plan; this is the safety net (and the gate any future
plan source must pass)."""
import re

from server import config
from .model import BLOCKED
from .registry import REGISTRY

REF = re.compile(r"^\$(\d+)\.(\w+)$")
MAX_STEPS = 8


class PlanError(Exception):
    pass


def validate(plan: dict) -> dict:
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps or len(steps) > MAX_STEPS:
        raise PlanError("steps missing or too many")
    seen = set()
    for s in steps:
        t = REGISTRY.get(s.get("tool"))
        if not t or t.level == BLOCKED:
            raise PlanError(f"tool not allowed: {s.get('tool')}")
        args = s.get("args", {}) or {}
        required = {k for k, v in t.args.items() if not v.endswith("?")}
        if not required <= set(args) or not set(args) <= set(t.args):
            raise PlanError(f"{t.name} takes args {list(t.args)} (required: {sorted(required)})")
        for v in args.values():
            if not isinstance(v, str):
                raise PlanError("all args must be strings")
            m = REF.match(v)
            if m and int(m.group(1)) not in seen:
                raise PlanError(f"bad reference {v}")
        s["args"] = args
        s["id"] = int(s["id"])
        seen.add(s["id"])
    return plan
