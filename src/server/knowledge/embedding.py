"""Embedder used by the knowledge base. Default: the organisation's embedding model through llm.embed (Ollama).
Swap by passing any object with embed_documents(list[str]) and embed_query(str) to KnowledgeBase (tests do)."""
from server import llm


class LLMEmbedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out = []
        for i in range(0, len(texts), 32):
            out.extend(llm.embed(texts[i:i + 32], "search_document: "))
        return out

    def embed_query(self, text: str) -> list[float]:
        return llm.embed([text], "search_query: ")[0]
