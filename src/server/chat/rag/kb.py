from server import config
from server.knowledge import router
from server.knowledge.store import get_kb
from .base import Passage, Retriever
from .registry import register


@register("kb")
class KBRetriever(Retriever):
    """ChromaDB knowledge base with two spaces. Searches the space the query points to; falls back to the other one.
    Only passages at or above KB_MIN_SCORE count as relevant, otherwise nothing is returned (and strict chat refuses)."""
    name = "kb"

    def __init__(self, kb=None):
        self._kb = kb

    @property
    def kb(self):
        return self._kb or get_kb()

    def retrieve(self, session, query, k=5) -> list[Passage]:
        for space in router.allowed_spaces(query, session.user.id):
            hits = [h for h in self.kb.query(space, query, k) if h.score >= config.KB_MIN_SCORE]
            if hits:
                return [Passage(h.text, f"{h.source} p.{h.page}", h.score, {"space": h.space, **h.meta}) for h in hits]
        return []
