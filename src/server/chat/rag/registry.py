"""Retriever registry. A retriever is enabled by name in RAG_RETRIEVERS (comma separated), either a name registered
with @register("name") or a dotted path "package.module:ClassName" (no code change needed to plug one in)."""
import importlib
import logging

from server import config
from .base import Retriever
from .null import NullRetriever

log = logging.getLogger("rag")
_BUILTIN: dict[str, type[Retriever]] = {"null": NullRetriever}


def register(name: str):
    def deco(cls):
        _BUILTIN[name] = cls
        return cls
    return deco


def _load(spec: str) -> Retriever:
    if spec in _BUILTIN:
        return _BUILTIN[spec]()
    if ":" in spec:
        mod, _, cls = spec.partition(":")
        return getattr(importlib.import_module(mod), cls)()
    raise ValueError(f"Unknown retriever '{spec}'. Register it with @register or use 'package.module:Class'.")


def build_retrievers(specs=None) -> list[Retriever]:
    from . import kb  # noqa: F401  (registers the built-in 'kb' retriever)
    out = []
    for spec in (config.RAG_RETRIEVERS if specs is None else specs):
        try:
            out.append(_load(spec))
        except Exception:
            log.exception("could not load retriever %s", spec)      # a broken plug-in must not take chat down
    return out
