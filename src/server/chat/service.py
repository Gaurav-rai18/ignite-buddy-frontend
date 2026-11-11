"""
Chat = the NON-deterministic path (anything the command engine does not recognise).

    retrieve (RAG, pluggable)  ->  build prompt  ->  stream from the LLM

Today no retriever is configured, so retrieval returns nothing and this is plain LLM chat. The day a real
knowledge base exists you implement `Retriever`, enable it with RAG_RETRIEVERS=..., and chat uses it. No other file changes.
"""
import logging
import re

from server import config, llm
from shared import protocol as P
from . import prompts
from .rag.base import Passage
from .rag.personal_docs import PersonalDocs
from .rag.registry import build_retrievers

log = logging.getLogger("chat")


_FOLLOWUP = re.compile(r"\b(it|its|this|that|these|those|they|them|their|he|she|more|also|else|again|specifically|"
                       r"in detail|elaborate|example|another|same|previous|above|earlier|the (?:first|second|third|last) one)\b", re.I)


def looks_like_followup(text: str) -> bool:
    """Cheap test (no model): short, or points back at something said before. Only these trigger query rewriting."""
    return len(text.split()) < 8 or bool(_FOLLOWUP.search(text))


class ChatService:
    def __init__(self, retrievers=None, strict=None):
        self.retrievers = build_retrievers() if retrievers is None else list(retrievers)
        self.strict = config.RAG_STRICT if strict is None else strict       # True: answer only from retrieved passages
        self.personal_docs = PersonalDocs()

    def retrieve(self, session, query: str) -> list[Passage]:
        """Ask every enabled retriever; one failing retriever never breaks the answer."""
        passages: list[Passage] = []
        for r in self.retrievers:
            try:
                passages.extend(r.retrieve(session, query, config.RAG_TOP_K))
            except Exception:
                log.exception("retriever %s failed; continuing without it", getattr(r, "name", r))
        passages.sort(key=lambda p: -p.score)
        return passages[:config.RAG_TOP_K]

    # ---------------- conversation memory ----------------
    def hydrate_history(self, session, query: str = ""):
        """New connection => the in-memory history is empty. Ask the PC's local database for the relevant earlier turns
        (last few + older ones related to this question). Silently skipped for clients without a local database."""
        try:
            res = session.ui.device_call(P.CHAT_CONTEXT, {"query": query})
        except Exception:
            return
        turns = res.data.get("turns") if res.status == P.OK else None
        if not isinstance(turns, list):
            return
        known = {m["content"] for m in session.history}
        fresh = [t for t in turns if isinstance(t, dict) and t.get("role") in ("user", "assistant")
                 and isinstance(t.get("content"), str) and t["content"] not in known]
        session.history[:0] = fresh[-12:]

    def condense(self, session, text: str) -> str:
        """Agentic step: turn a follow-up ("how does map work in it?") into a standalone query using the conversation.
        The fast model is used ONLY for follow-ups; on any failure fall back to prefixing the previous question."""
        if not session.history or not looks_like_followup(text):
            return text
        try:
            out = llm.chat_text(prompts.condense_messages(session.history, text), model=config.FAST_MODEL, temperature=0.0)
            out = " ".join(out.strip().strip("\"'").split())[:300]
            if len(out) >= 3:
                return out
        except Exception:
            log.warning("query condensation failed; using the previous question", exc_info=False)
        prev = next((m["content"] for m in reversed(session.history) if m["role"] == "user"), "")
        return f"{prev} {text}".strip()

    def retrieve_with_followups(self, session, text: str):
        """Attempt retrieval using the standalone condensed query first, falling back to the raw query wording.

        Returns a tuple of (passages, winning_query). If no relevant passages are found, returns an
        empty list and the resolved query string (or the raw text if no queries were formed).
        """
        queries = []
        for q in (self.condense(session, text), text):
            if q and q not in queries:
                queries.append(q)
        for q in queries:
            passages = self.retrieve(session, q)
            if passages:
                return passages, q
        return [], (queries[0] if queries else text)

    def stream_reply(self, session, text: str):
        """Generator yielding streamed answer tokens.

        Under strict mode (default):
        - If no relevant passages are found, emits the standard refusal text without invoking the LLM.
        - If the LLM determines the retrieved passages do not answer the prompt, it yields the
          NOT_IN_CONTEXT sentinel, which is intercepted and replaced with the friendly refusal text.
        - Preserves legitimate short model answers (such as single-word responses) without false refusals.
        """
        if not session.history:
            self.hydrate_history(session, text)
        passages, _query = self.retrieve_with_followups(session, text)
        if not self.strict:
            yield from llm.chat_stream(prompts.chat_messages(session.history, text, passages, config.CHAT_HISTORY_TURNS))
            return
        if not passages:
            yield prompts.NOT_FOUND
            return
        head, decided = "", False
        for chunk in llm.chat_stream(prompts.strict_messages(session.history, text, passages, config.CHAT_HISTORY_TURNS)):
            if decided:
                yield chunk
                continue
            head += chunk or ""
            if len(head.lstrip()) >= len(prompts.SENTINEL):          # enough text to tell a refusal from an answer
                decided = True
                if head.lstrip().startswith(prompts.SENTINEL):
                    yield prompts.NOT_FOUND
                    return
                yield head
        if not decided and head:                                     # very short answer
            stripped = head.strip()
            yield prompts.NOT_FOUND if stripped == prompts.SENTINEL else head

    def stream_docs_answer(self, session, question: str):
        """'What do my documents say about X?': strict, answers only from the user's own indexed documents."""
        try:
            passages = self.personal_docs.retrieve(session, question, config.RAG_TOP_K)
        except Exception:
            log.exception("personal docs retrieval failed")
            passages = []
        if not passages:
            yield "No documents are indexed yet. Use /index <folder> first."
            return
        yield from llm.chat_stream(prompts.docs_messages(question, passages))

    def stream_rag_answer(self, session, question: str):
        """Execute RAG question-answering with local SQLite conversation memory and hybrid retrieval.

        1. Reads the past last n conversations from local SQLite memory.
        2. Evaluates whether query-related content is already contained within recent memory.
        3. If query-related chunks are not in the last n conversation tokens/turns, performs
           keyword search and HNSW vector search across the knowledge base and personal documents.
        4. Provides conversation memory and relevant retrieved documents to the gpt-oss:20b LLM
           with a 128K context window.
        5. Persists the completed turn to the local SQLite storage.
        """
        import re
        from pathlib import Path

        # 1. Read past last n conversations from memory stored in local SQLite
        memory: list[dict] = []
        if hasattr(session, "store") and session.store:
            try:
                memory = session.store.get_chat_history(config.RAG_MEMORY_TURNS)
            except Exception:
                log.exception("failed reading chat history from local SQLite store")
        if not memory and getattr(session, "history", None):
            memory = list(session.history[-config.RAG_MEMORY_TURNS * 2:])

        # 2. Check if query-related chunks are in the last n conversation turns
        tokens = [w.lower() for w in re.findall(r"\w+", question) if len(w) >= 3]
        memory_text = " ".join(m.get("content", "").lower() for m in memory)
        matching_tokens = [tok for tok in tokens if tok in memory_text]
        in_memory = len(matching_tokens) >= max(1, len(tokens) // 2) if tokens else False

        # 3. Retrieve external documents if needed (or to augment memory)
        passages: list[Passage] = []
        if not in_memory:
            # Perform keyword search across knowledge base spaces
            try:
                from server.knowledge.store import get_kb
                kb = get_kb()
                for space in ("ignite", "general"):
                    kw_hits = kb.keyword_search(space, question, k=config.RAG_TOP_K)
                    for h in kw_hits:
                        passages.append(Passage(h.text, f"{h.source} p.{h.page}", h.score, {"space": h.space, "method": "keyword"}))
            except Exception as e:
                log.warning("keyword search in KB unavailable: %s", e)

            # Perform keyword search across user's personal documents
            if hasattr(session, "store") and session.store:
                try:
                    from server.knowledge.personal import PersonalVectors
                    pv = PersonalVectors()
                    for doc, meta, score in pv.keyword_search_documents(session.store.key, question, k=config.RAG_TOP_K):
                        fname = Path(meta.get("path", "")).name or "document"
                        passages.append(Passage(doc, f"{fname} p.{meta.get('page', 1)}", float(score), {"method": "keyword", **meta}))
                except Exception as e:
                    log.warning("keyword search in personal documents unavailable: %s", e)

            # Perform HNSW vector similarity search
            try:
                passages.extend(self.retrieve(session, question))
            except Exception as e:
                log.warning("HNSW vector search unavailable: %s", e)

            # Deduplicate passages
            seen_texts = set()
            unique_passages = []
            for p in sorted(passages, key=lambda x: -x.score):
                lead = " ".join(p.text.split()[:20])
                if lead not in seen_texts:
                    seen_texts.add(lead)
                    unique_passages.append(p)
            passages = unique_passages[:config.RAG_TOP_K * 2]

        # 4. Assemble prompt with memory and relevant retrieved documents for gpt-oss:20b
        messages = prompts.rag_prompt_messages(memory, question, passages, turns=config.RAG_MEMORY_TURNS)

        # 5. Stream response from LLM and collect completed text
        full_reply_parts = []
        try:
            for chunk in llm.chat_stream(messages, model=config.CHAT_MODEL):
                if chunk:
                    full_reply_parts.append(chunk)
                    yield chunk
        finally:
            full_reply = "".join(full_reply_parts).strip()
            if full_reply and hasattr(session, "store") and session.store:
                try:
                    session.store.add_chat_turn(question, full_reply)
                except Exception:
                    log.exception("failed persisting chat turn to local SQLite")


_service: ChatService | None = None


def get_chat_service() -> ChatService:
    global _service
    if _service is None:
        _service = ChatService()
    return _service
