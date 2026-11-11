"""Embeddings of ONE trainee's private content (their indexed documents, their daily/session summaries) in ChromaDB,
tagged with the trainee's key and always queried with a `user` filter. Relational data lives in PostgreSQL/SQLite; vectors never do."""
from .chunk import chunk_text, compute_chunk_hash
from .store import get_kb, _MemoryChromaCollection


def _w(user: str, **more) -> dict:
    conds = [{"user": user}, *({k: v} for k, v in more.items())]
    return {"$and": conds} if len(conds) > 1 else conds[0]


class PersonalVectors:
    DOCS, SUMS = "personal_docs", "personal_summaries"

    def __init__(self, kb=None):
        self._kb = kb

    @property
    def kb(self):
        return self._kb or get_kb()

    def _col(self, name: str):
        """Retrieve or initialize personal vector collections indexed with HNSW."""
        kb = self.kb
        if getattr(kb, "_use_chroma", False) and kb.client:
            try:
                return kb.client.get_or_create_collection(
                    name=name,
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
        if not hasattr(kb, "_memory_cols"):
            kb._memory_cols = {}
        if name not in kb._memory_cols:
            kb._memory_cols[name] = _MemoryChromaCollection(name=name)
        return kb._memory_cols[name]

    # ---------------- documents ----------------
    def known_hashes(self, user: str) -> dict[str, str]:
        got = self._col(self.DOCS).get(where=_w(user), include=["metadatas"])
        return {m["path"]: m["file_hash"] for m in got["metadatas"]}

    def put_document(self, user: str, path: str, file_hash: str, pages) -> int:
        seen_hashes = set()
        items = []
        for pg, txt in pages:
            for piece in chunk_text(txt, seen_hashes=seen_hashes, deduplicate=True):
                h = compute_chunk_hash(piece)
                seen_hashes.add(h)
                items.append((pg, piece, h))

        col = self._col(self.DOCS)
        col.delete(where=_w(user, path=path))
        if not items:
            return 0
        vectors = self.kb.embedder.embed_documents([c for _, c, _ in items])
        for i in range(0, len(items), 200):
            part = items[i:i + 200]
            col.add(
                ids=[f"{user}:{file_hash[:8]}:{h[:16]}" for _, _, h in part],
                documents=[c for _, c, _ in part],
                embeddings=vectors[i:i + 200],
                metadatas=[
                    {
                        "user": user,
                        "path": path,
                        "page": int(pg),
                        "file_hash": file_hash,
                        "chunk_hash": h,
                    }
                    for pg, _, h in part
                ],
            )
        return len(items)

    def search_documents(self, user: str, query: str, k: int = 5):
        """Vector similarity search over the user's indexed private documents.

        Clamps n_results to the total number of items in the collection so ChromaDB
        does not raise a ValueError if fewer documents exist than the requested k.
        Returns a list of (document_text, metadata_dict, similarity_score) tuples.
        """
        col = self._col(self.DOCS)
        total = col.count()
        if total == 0:
            return []
        n = min(k, total)
        res = col.query(
            query_embeddings=[self.kb.embedder.embed_query(query)],
            n_results=n,
            where=_w(user),
            include=["documents", "metadatas", "distances"],
        )
        if not res.get("documents") or not res["documents"][0]:
            return []
        return [(doc, meta, 1.0 - dist) for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])]

    def keyword_search_documents(self, user: str, query: str, k: int = 5):
        """Lexical and keyword search over the user's indexed private documents."""
        import re
        col = self._col(self.DOCS)
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
                found = col.get(where=_w(user), where_document={"$contains": tok}, limit=min(50, total), include=["documents", "metadatas"])
                for did, doc, meta in zip(found.get("ids", []), found.get("documents", []), found.get("metadatas", [])):
                    if did not in seen_ids:
                        seen_ids.add(did)
                        matched_chunks.append((did, doc, meta))
            except Exception:
                pass

        if not matched_chunks:
            found = col.get(where=_w(user), limit=min(100, total), include=["documents", "metadatas"])
            for did, doc, meta in zip(found.get("ids", []), found.get("documents", []), found.get("metadatas", [])):
                matched_chunks.append((did, doc, meta))

        scored = []
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
                scored.append((doc, meta, min(0.99, 0.4 + score * 0.1)))

        scored.sort(key=lambda x: -x[2])
        return scored[:k]

    # ---------------- summaries ----------------
    def put_summaries(self, user: str, day: str, items):
        """Store daily/session summary embeddings for a trainee.

        items is a list of (kind, text) tuples.
        """
        col = self._col(self.SUMS)
        col.delete(where=_w(user, day=day))
        if not items:
            return
        vectors = self.kb.embedder.embed_documents([f"{day} {t[:1500]}" for _, t in items])
        col.add(ids=[f"{user}:{day}:{i}" for i in range(len(items))], documents=[t for _, t in items], embeddings=vectors,
                metadatas=[{"user": user, "day": day, "kind": k} for k, _ in items])

    def search_summaries(self, user: str, query: str, k: int = 3):
        """Vector similarity search over past daily and session activity summaries.

        Clamps n_results to the total number of items in the collection so ChromaDB
        does not raise a ValueError if fewer summaries exist than the requested k.
        Returns a list of (day, kind, document_text) tuples.
        """
        col = self._col(self.SUMS)
        total = col.count()
        if total == 0:
            return []
        n = min(k, total)
        res = col.query(
            query_embeddings=[self.kb.embedder.embed_query(query)],
            n_results=n,
            where=_w(user),
            include=["documents", "metadatas"],
        )
        if not res.get("documents") or not res["documents"][0]:
            return []
        return [(m["day"], m["kind"], d) for d, m in zip(res["documents"][0], res["metadatas"][0])]

    # ---------------- housekeeping ----------------
    def count(self, user: str) -> dict:
        return {name: len(self._col(name).get(where=_w(user), include=[])["ids"]) for name in (self.DOCS, self.SUMS)}

    def delete_user(self, user: str):
        for name in (self.DOCS, self.SUMS):
            self._col(name).delete(where=_w(user))
