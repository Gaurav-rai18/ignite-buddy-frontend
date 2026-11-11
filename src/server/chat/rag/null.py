from .base import Passage, Retriever


class NullRetriever(Retriever):
    """Default until a real knowledge base exists: retrieves nothing, so chat is plain LLM chat."""
    name = "null"

    def retrieve(self, session, query, k=5) -> list[Passage]:
        return []
