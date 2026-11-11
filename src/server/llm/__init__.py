"""LLM access layer (LangChain ChatOllama -> the organisation's Ollama server).

Public API (unchanged by the client/server split; only the server may import this package):
    chat_json(system, user, model=None) -> dict
    chat_stream(messages, model=None)   -> iterator of text chunks
    chat_text(messages, model=None, temperature=0.3) -> str
    embed(texts, prefix) -> list[list[float]]
    supports_vision(model) -> bool

Modules:
    network.py   proxy / TLS (Zscaler) / auth headers / timeouts -> httpx kwargs
    client.py    cached ChatOllama / OllamaEmbeddings factories
    messages.py  app message dicts -> LangChain messages (incl. images)
    errors.py    turns low-level failures into readable LLMError messages
    api.py       the five functions above
    diagnose.py  `python -m server.llm.diagnose` connectivity check
"""
from .api import chat_json, chat_stream, chat_text, embed, supports_vision
from .errors import LLMError

__all__ = ["chat_json", "chat_stream", "chat_text", "embed", "supports_vision", "LLMError"]
