"""
RAG contract. Implement `Retriever`, register it (see registry.py), and the chat path starts using it: nothing else
in the codebase changes.

    class KnowledgeBase(Retriever):
        name = "kb"
        def retrieve(self, session, query, k=5):
            hits = my_vector_store.search(query, k)          # your embeddings / index / API
            return [Passage(text=h.text, source=h.title, score=h.score) for h in hits]

`session` carries the user (session.user.id / role / batch) so a retriever can filter by who is asking, and the
per-user store (session.store) for per-user corpora. Retrievers run in a worker thread: blocking I/O is fine.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Passage:
    text: str
    source: str = ""                  # shown to the model so it can cite: "[source]"
    score: float = 0.0
    meta: dict = field(default_factory=dict)


class Retriever(ABC):
    name: str = "retriever"

    @abstractmethod
    def retrieve(self, session, query: str, k: int = 5) -> list[Passage]:
        """Return the best passages for `query`, best first. Return [] when nothing relevant."""


class Ingestor(ABC):
    """Optional: a corpus that accepts new content (e.g. the personal-documents index)."""

    @abstractmethod
    def ingest(self, session, documents: list[dict]) -> int:
        """documents: [{"id": str, "source": str, "pages": [(n, text), ...], "hash": str}] -> chunks stored"""
