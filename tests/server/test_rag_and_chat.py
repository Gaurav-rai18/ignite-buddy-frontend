import pytest
from server import config, llm
from server.chat import prompts
from server.chat.rag.base import Passage, Retriever
from server.chat.rag.registry import build_retrievers, register
from server.chat.service import ChatService


def capture_llm(monkeypatch):
    seen = {}
    def fake(messages, **k):
        seen["messages"] = messages
        yield "ok"
    monkeypatch.setattr(llm, "chat_stream", fake)
    return seen


def test_default_is_plain_chat(session, monkeypatch):
    seen = capture_llm(monkeypatch)
    assert build_retrievers([]) == []
    svc = ChatService(retrievers=[], strict=False)
    assert "".join(svc.stream_reply(session, "what is a closure")) == "ok"
    msgs = seen["messages"]
    assert msgs[-1] == {"role": "user", "content": "what is a closure"} and "Reference passages" not in msgs[0]["content"]


@register("fake_kb")
class FakeKB(Retriever):
    name = "fake_kb"
    def retrieve(self, session, query, k=5):
        return [Passage("Python closures capture variables.", source="python-handbook p.3", score=0.9)]


class Broken(Retriever):
    def retrieve(self, session, query, k=5): raise RuntimeError("vector db down")


def test_plugging_in_a_retriever_needs_no_other_change(session, monkeypatch):
    seen = capture_llm(monkeypatch)
    svc = ChatService(retrievers=build_retrievers(["fake_kb"]), strict=False)
    list(svc.stream_reply(session, "what is a closure"))
    user = seen["messages"][-1]["content"]
    assert "python-handbook p.3" in user and "closures capture" in user and "what is a closure" in user
    assert "cite" in seen["messages"][0]["content"].lower()
    assert session.history == []                       # injected context is never stored in history


def test_dotted_path_and_failure_isolation(session, monkeypatch):
    seen = capture_llm(monkeypatch)
    assert len(build_retrievers(["tests.server.test_rag_and_chat:FakeKB", "no.such:Thing"])) == 1   # bad plug-in skipped
    svc = ChatService(retrievers=[Broken(), FakeKB()], strict=False)
    assert "".join(svc.stream_reply(session, "q")) == "ok"        # one retriever failing does not break chat
    assert "python-handbook" in seen["messages"][-1]["content"]


def test_history_is_trimmed():
    hist = [{"role": "user", "content": str(i)} for i in range(40)]
    assert len(prompts.chat_messages(hist, "x", [], 10)) == 12


def test_docs_answer_without_index(session, monkeypatch):
    monkeypatch.setattr(llm, "embed", lambda *a, **k: [[0.1, 0.2]])
    out = "".join(ChatService(retrievers=[]).stream_docs_answer(session, "what do my docs say"))
    assert "/index" in out


def test_personal_docs_ingest_and_retrieve(session, monkeypatch):
    import numpy as np
    def emb(texts, prefix=""):
        return [[1.0, 0.0] if "deadline" in t.lower() else [0.0, 1.0] for t in texts]
    monkeypatch.setattr(llm, "embed", emb)
    from server.chat.rag.personal_docs import PersonalDocs
    d = PersonalDocs()
    assert d.ingest(session, [{"id": "/x/plan.txt", "source": "plan", "hash": "h1",
                               "pages": [(1, "The project deadline is 5 Nov."), (2, "Lunch menu")]}]) == 2
    top = d.retrieve(session, "when is the deadline", 1)[0]
    assert "5 Nov" in top.text and top.source == "plan.txt p.1"
    assert d.known_hashes(session) == {"/x/plan.txt": "h1"}
