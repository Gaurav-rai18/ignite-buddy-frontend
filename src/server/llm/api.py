"""The functions the rest of the app calls. Same signatures as the old ollama-based llm.py."""
import json

from server import config
from .client import chat_model, embedding_model, raw_client
from .errors import explain
from .messages import to_langchain


def chat_json(system: str, user: str, model: str | None = None) -> dict:
    """Deterministic JSON output (used by the planner)."""
    llm = chat_model(model or config.FAST_MODEL, 0.0, config.NUM_CTX_PLANNER, True)
    try:
        r = llm.invoke(to_langchain([{"role": "system", "content": system}, {"role": "user", "content": user}]))
    except Exception as e:
        raise explain(e) from e
    return json.loads(r.content)


def chat_stream(messages: list[dict], model: str | None = None):
    """Yield text chunks."""
    llm = chat_model(model or config.CHAT_MODEL, 0.3, config.NUM_CTX_CHAT)
    try:
        for chunk in llm.stream(to_langchain(messages)):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        raise explain(e) from e


def chat_text(messages: list[dict], model: str | None = None, temperature: float = 0.3) -> str:
    """Non-streaming completion (used for map steps and background jobs)."""
    llm = chat_model(model or config.CHAT_MODEL, float(temperature), config.NUM_CTX_CHAT)
    try:
        return llm.invoke(to_langchain(messages)).content.strip()
    except Exception as e:
        raise explain(e) from e


import hashlib

_EMBED_CACHE: dict[str, list[float]] = {}


def _embed_cache_key(prefix: str, text: str) -> str:
    norm = " ".join(text.split())
    return hashlib.sha256(f"{prefix}:{norm}".encode("utf-8")).hexdigest()


def embed(texts: list[str], prefix: str) -> list[list[float]]:
    """
    Produce vector embeddings with chunk-level deduplication and caching.
    Duplicate chunks in the batch are embedded only once to conserve compute.
    """
    if not texts:
        return []

    emb = embedding_model(config.EMBED_MODEL)
    result: list[list[float] | None] = [None] * len(texts)
    to_embed_texts: list[str] = []
    to_embed_indices: list[list[int]] = []
    seen_in_batch: dict[str, int] = {}

    for idx, t in enumerate(texts):
        key = _embed_cache_key(prefix, t)
        if key in _EMBED_CACHE:
            result[idx] = _EMBED_CACHE[key]
        elif key in seen_in_batch:
            to_embed_indices[seen_in_batch[key]].append(idx)
        else:
            seen_in_batch[key] = len(to_embed_texts)
            to_embed_texts.append(t)
            to_embed_indices.append([idx])

    if to_embed_texts:
        try:
            new_vectors: list[list[float]] = []
            for i in range(0, len(to_embed_texts), 32):
                batch = to_embed_texts[i:i + 32]
                new_vectors.extend(emb.embed_documents([prefix + t for t in batch]))

            for t, indices, vec in zip(to_embed_texts, to_embed_indices, new_vectors):
                key = _embed_cache_key(prefix, t)
                _EMBED_CACHE[key] = vec
                for idx in indices:
                    result[idx] = vec
        except Exception as e:
            raise explain(e) from e

    return [v if v is not None else [] for v in result]


_vision_cache: dict[str, bool] = {}


def supports_vision(model: str) -> bool:
    """Ask the server whether a model accepts images (needs a recent Ollama that reports capabilities)."""
    if model not in _vision_cache:
        try:
            caps = getattr(raw_client().show(model), "capabilities", None) or []
            _vision_cache[model] = "vision" in caps
        except Exception:
            _vision_cache[model] = False
    return _vision_cache[model]
