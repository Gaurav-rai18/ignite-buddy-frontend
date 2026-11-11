"""Deterministic command engine. `from server import commands` registers all skills."""
from . import skills  # noqa: F401  (registers tools + rules)
from .executor import run_plan
from .parser import RULES, looks_like_command, parse, parse_mixed
from .registry import REGISTRY
from .validate import PlanError, validate

__all__ = ["parse", "parse_mixed", "validate", "run_plan", "looks_like_command", "REGISTRY", "RULES", "PlanError"]
