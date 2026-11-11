"""Chat path: retrieve (optional RAG) → prompt → stream LLM tokens.

``get_chat_service()`` returns the process-wide ChatService. Retrievers are
pluggable via ``chat.rag.registry`` (KB, personal docs, or null).
"""
from .service import ChatService, get_chat_service

__all__ = ["ChatService", "get_chat_service"]
