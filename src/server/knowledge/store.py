"""
Knowledge base on ChromaDB with pure-Python fallback. Two spaces = two collections:
    "ignite"   Ignite-programme material (onboarding, schedules, assessments, programme FAQs)
    "general"  general technical / company knowledge
Vectors are produced by OUR embedder (not Chroma's default, which would download a model), cosine similarity.
Includes chunk-level SHA-256 content hashing to deduplicate chunks and avoid storing redundant vectors.
"""
import math
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

from server import config
from .chunk import chunk_text, compute_chunk_hash
from .embedding import LLMEmbedder

SPACES = ("ignite", "general")


@dataclass(frozen=True)
class Hit:
    text: str
    source: str
    page: int
    score: float                    # cosine similarity, higher = more relevant
    space: str
    meta: dict = field(default_factory=dict)


class _MemoryChromaCollection:
    """
    Lightweight in-memory vector store matching ChromaDB collection semantics.
    Provides a seamless fallback when ChromaDB native C-extensions (like cygrpc)
    are blocked by platform application control policies.
    """
    def __init__(self, name: str):
        self.name = name
        self._items: dict[str, dict] = {}

    def count(self) -> int:
        return len(self._items)

    def get(self, where=None, where_document=None, limit=None, include=None):
        out_ids, out_docs, out_metas = [], [], []
        for did, item in self._items.items():
            if where:
                match = True
                for k, v in where.items():
                    if item["metadata"].get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            if where_document and "$contains" in where_document:
                sub = where_document["$contains"].lower()
                if sub not in item["document"].lower():
                    continue
            out_ids.append(did)
            out_docs.append(item["document"])
            out_metas.append(item["metadata"])
            if limit and len(out_ids) >= limit:
                break
        res = {}
        inc = include or ["documents", "metadatas", "ids"]
        if "ids" in inc or include is None:
            res["ids"] = out_ids
        if "documents" in inc:
            res["documents"] = out_docs
        if "metadatas" in inc:
            res["metadatas"] = out_metas
        return res

    def delete(self, where=None):
        if not where:
            self._items.clear()
            return
        to_del = []
        for did, item in self._items.items():
            match = True
            for k, v in where.items():
                if item["metadata"].get(k) != v:
                    match = False
                    break
            if match:
                to_del.append(did)
        for did in to_del:
            self._items.pop(did, None)

    def add(self, ids, documents, metadatas=None, embeddings=None):
        metas = metadatas or [{}] * len(ids)
        embs = embeddings or [[]] * len(ids)
        for did, doc, meta, emb in zip(ids, documents, metas, embs):
            self._items[did] = {
                "document": doc,
                "metadata": dict(meta),
                "embedding": list(emb) if emb else [],
            }

    def query(self, query_embeddings=None, n_results=5, where=None, include=None):
        if not self._items or not query_embeddings:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        q_emb = query_embeddings[0]

        def dist(item):
            v = item["embedding"]
            if not v or not q_emb:
                return 1.0
            dot = sum(a * b for a, b in zip(q_emb, v))
            n1 = math.sqrt(sum(a * a for a in q_emb)) or 1.0
            n2 = math.sqrt(sum(b * b for b in v)) or 1.0
            sim = dot / (n1 * n2)
            return max(0.0, 1.0 - sim)

        candidates = list(self._items.values())
        if where:
            candidates = [it for it in candidates if all(it["metadata"].get(k) == v for k, v in where.items())]

        candidates.sort(key=dist)
        top = candidates[:n_results]
        return {
            "documents": [[it["document"] for it in top]],
            "metadatas": [[it["metadata"] for it in top]],
            "distances": [[dist(it) for it in top]],
        }


class KnowledgeBase:
    def __init__(self, path=None, embedder=None):
        self.path = Path(path or config.KB_PATH)
        self.path.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder or LLMEmbedder()
        self._lock = threading.Lock()
        self._memory_cols: dict[str, _MemoryChromaCollection] = {}
        self._use_chroma = False

        try:
            import chromadb
            from chromadb.config import Settings
            self.client = chromadb.PersistentClient(
                path=str(self.path),
                settings=Settings(anonymized_telemetry=False),
            )
            self._use_chroma = True
        except Exception:
            self.client = None
            self._use_chroma = False

    def _col(self, space: str):
        """Retrieve or initialize a collection with cosine similarity indexing."""
        if space not in SPACES:
            raise ValueError(f"unknown space '{space}' (use one of {SPACES})")
        if self._use_chroma and self.client:
            try:
                return self.client.get_or_create_collection(
                    name=f"kb_{space}",
                    metadata={
                        "hnsw:space": "cosine",
                        "hnsw:construction_ef": 128,
                        "hnsw:M": 16,
                        "hnsw:search_ef": 100,
                    },
                    embedding_function=None,
                )
            except Exception:
                pass
        if space not in self._memory_cols:
            self._memory_cols[space] = _MemoryChromaCollection(name=f"kb_{space}")
        return self._memory_cols[space]

    # ---------------- write ----------------
    def source_hash(self, space: str, source: str) -> str | None:
        got = self._col(space).get(where={"source": source}, limit=1, include=["metadatas"])
        return got["metadatas"][0].get("file_hash") if got["metadatas"] else None

    def delete_source(self, space: str, source: str):
        with self._lock:
            self._col(space).delete(where={"source": source})

    def add_document(self, space: str, source: str, pages, file_hash: str) -> int:
        """
        Replace stored chunks for `source` with these pages.
        Uses SHA-256 chunk content hashing to suppress duplicate chunks across pages.
        Returns the number of unique chunks stored.
        """
        docs, metas, ids = [], [], []
        seen_hashes: set[str] = set()

        for page, text in pages:
            for piece in chunk_text(text, seen_hashes=seen_hashes, deduplicate=True):
                h = compute_chunk_hash(piece)
                seen_hashes.add(h)
                docs.append(piece)
                metas.append({
                    "source": source,
                    "page": int(page),
                    "file_hash": file_hash,
                    "chunk_hash": h,
                    "space": space,
                })
                # Deterministic ID using file_hash and chunk_hash prevents duplicate embeddings
                ids.append(f"{file_hash[:12]}:{h[:16]}")

        self.delete_source(space, source)
        if not docs:
            return 0

        vectors = self.embedder.embed_documents(docs)
        with self._lock:
            col = self._col(space)
            for i in range(0, len(docs), 200):
                col.add(
                    ids=ids[i:i + 200],
                    documents=docs[i:i + 200],
                    metadatas=metas[i:i + 200],
                    embeddings=vectors[i:i + 200],
                )
        return len(docs)

    # ---------------- read ----------------
    def query(self, space: str, text: str, k: int = 5) -> list[Hit]:
        col = self._col(space)
        if col.count() == 0:
            return []
        res = col.query(
            query_embeddings=[self.embedder.embed_query(text)],
            n_results=min(k, col.count()),
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            hits.append(Hit(doc, meta.get("source", ""), int(meta.get("page", 1)), 1.0 - float(dist), space, dict(meta)))
        return sorted(hits, key=lambda h: -h.score)

    def keyword_search(self, space: str, query: str, k: int = 5) -> list[Hit]:
        """Perform exact and lexical keyword retrieval across indexed document chunks in the given space."""
        col = self._col(space)
        total = col.count()
        if total == 0:
            return []

        tokens = [w.lower() for w in re.findall(r"\w+", query) if len(w) >= 3]
        if not tokens:
            tokens = [query.lower().strip()] if query.strip() else []
        if not tokens:
            return []

        matched_chunks = []
        seen_ids = set()
        for tok in tokens[:5]:
            try:
                found = col.get(where_document={"$contains": tok}, limit=min(50, total), include=["documents", "metadatas"])
                for did, doc, meta in zip(found["ids"], found["documents"], found["metadatas"]):
                    if did not in seen_ids:
                        seen_ids.add(did)
                        matched_chunks.append((did, doc, meta))
            except Exception:
                pass

        if not matched_chunks:
            found = col.get(limit=min(200, total), include=["documents", "metadatas"])
            for did, doc, meta in zip(found.get("ids", []), found.get("documents", []), found.get("metadatas", [])):
                matched_chunks.append((did, doc, meta))

        scored_hits = []
        query_lower = query.lower()
        for did, doc, meta in matched_chunks:
            doc_lower = doc.lower()
            score = 0.0
            for tok in tokens:
                if tok in doc_lower:
                    score += 1.0 + (doc_lower.count(tok) * 0.1)
            if query_lower in doc_lower:
                score += 3.0
            if score > 0:
                scored_hits.append(
                    Hit(
                        doc,
                        meta.get("source", ""),
                        int(meta.get("page", 1)),
                        min(0.99, 0.4 + score * 0.1),
                        space,
                        dict(meta),
                    )
                )

        scored_hits.sort(key=lambda h: -h.score)
        return scored_hits[:k]

    def stats(self) -> dict:
        out = {}
        for sp in SPACES:
            col = self._col(sp)
            metas = col.get(include=["metadatas"])["metadatas"] if col.count() else []
            out[sp] = {"chunks": col.count(), "sources": sorted({m.get("source", "") for m in metas})}
        return out


_kb: KnowledgeBase | None = None
_kb_lock = threading.Lock()


def get_kb() -> KnowledgeBase:
    global _kb
    with _kb_lock:
        if _kb is None:
            _kb = KnowledgeBase()
        return _kb


def set_kb(kb: KnowledgeBase | None):
    """Tests / alternative backends."""
    global _kb
    _kb = kb
