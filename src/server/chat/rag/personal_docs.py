"""
Personal-documents corpus: chunk -> embedding -> ChromaDB (filtered by trainee) -> cosine search.
The CLIENT reads the files (they live on its disk) and sends text; the server chunks, embeds and stores it.
"""
from server.knowledge.personal import PersonalVectors
from shared import protocol as P
from .base import Ingestor, Passage, Retriever


def _chunk(text: str, size=800, overlap=100):
    text = " ".join(text.split())
    for i in range(0, len(text), size - overlap):
        piece = text[i:i + size]
        if piece.strip():
            yield piece


class PersonalDocs(Retriever, Ingestor):
    name = "personal_docs"

    def __init__(self, vectors=None):
        self.vectors = vectors or PersonalVectors()

    # ---------- retrieval ----------
    def retrieve(self, session, query: str, k: int = 5) -> list[Passage]:
        out = []
        for text, meta, score in self.vectors.search_documents(session.store.key, query, k):
            fname = meta["path"].replace("\\", "/").rsplit("/", 1)[-1]
            out.append(Passage(text=text, source=f"{fname} p.{meta['page']}", score=float(score),
                               meta={"path": meta["path"], "page": meta["page"]}))
        return out

    # ---------- ingestion ----------
    def known_hashes(self, session) -> dict[str, str]:
        return self.vectors.known_hashes(session.store.key)

    def ingest(self, session, documents: list[dict]) -> int:
        return sum(self.vectors.put_document(session.store.key, d["id"], d["hash"], d["pages"]) for d in documents)

    def index_folder(self, session, folder: str, say=print) -> int:
        """Pull new/changed documents from the client machine, one file at a time (small messages)."""
        ui = session.ui
        res = ui.device_call(P.LIST_DOCUMENTS, {"folder": folder})
        if res.status != P.OK:
            raise RuntimeError(res.message or "The client could not list that folder.")
        known, total = self.known_hashes(session), 0
        for f in res.data.get("files", []):
            if known.get(f["path"]) == f["hash"]:
                continue                                          # unchanged -> skip
            r = ui.device_call(P.READ_DOCUMENT, {"path": f["path"]})
            if r.status != P.OK:
                say(f"skipped {f['path']}: {r.message}")
                continue
            pages = [(int(n), str(t)) for n, t in r.data.get("pages", [])]
            n = self.ingest(session, [{"id": f["path"], "source": f["path"], "hash": f["hash"], "pages": pages}])
            total += n
            say(f"indexed {f['path'].replace(chr(92), '/').rsplit('/', 1)[-1]} ({n} chunks)")
        return total
