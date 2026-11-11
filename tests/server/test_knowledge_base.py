import hashlib
import math
import re
import pytest
from server import config, llm
from server.chat import prompts
from server.chat.rag.kb import KBRetriever
from server.chat.service import ChatService
from server.domain import policy
from server.knowledge import router as kbrouter
from server.knowledge.extract import ExtractError, extract
from server.knowledge.ingest import ingest_path
from server.knowledge.store import KnowledgeBase


class FakeEmbedder:
    """Deterministic bag-of-words hashing: shared words => high cosine similarity (stands in for nomic-embed-text)."""
    DIM = 256
    def _vec(self, text):
        v = [0.0] * self.DIM
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            if len(w) > 2:
                v[int(hashlib.md5(w.encode()).hexdigest(), 16) % self.DIM] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        return [x / n for x in v]
    def embed_documents(self, texts): return [self._vec(t) for t in texts]
    def embed_query(self, text): return self._vec(text)


def make_pdf(path, text):
    """Smallest valid one-page PDF with real text."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"]
    stream = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET"
    objs += [f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += f"{i} 0 obj\n{o}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    path.write_bytes(out)


@pytest.fixture(autouse=True)
def low_threshold(monkeypatch):
    monkeypatch.setattr(config, 'KB_MIN_SCORE', 0.25)       # the bag-of-words fake embedder scores lower than a real model


@pytest.fixture
def docs(tmp_path):
    from docx import Document
    from pptx import Presentation
    d = tmp_path / "docs"; d.mkdir()
    make_pdf(d / "leave-policy.pdf", "Employees get twenty four days of annual leave per calendar year")
    (d / "git-guide.md").write_text("# Git\nUse git rebase to rewrite commit history. Use git merge to join branches.")
    (d / "wifi.txt").write_text("The office wifi password rotation happens every ninety days via the helpdesk portal.")
    doc = Document(); doc.add_heading("Ignite Assessment", 1)
    doc.add_paragraph("The Ignite assessment has three rounds: aptitude, coding and an interview with the batch mentor.")
    doc.save(d / "ignite-assessment.docx")
    prs = Presentation(); sl = prs.slides.add_slide(prs.slide_layouts[1])
    sl.shapes.title.text = "Ignite Onboarding"
    sl.placeholders[1].text = "Trainees receive laptops on day one and complete induction training in the first week."
    prs.save(d / "ignite-onboarding.pptx")
    (d / "image.png").write_bytes(b"x")
    return d


@pytest.fixture
def kb(tmp_path, docs):
    k = KnowledgeBase(tmp_path / "chroma", FakeEmbedder())
    ingest_path(k, "ignite", docs / "ignite-assessment.docx", say=lambda m: None)
    ingest_path(k, "ignite", docs / "ignite-onboarding.pptx", say=lambda m: None)
    for f in ("leave-policy.pdf", "git-guide.md", "wifi.txt"):
        ingest_path(k, "general", docs / f, say=lambda m: None)
    return k


def test_all_five_formats_extract(docs):
    for f, word in [("leave-policy.pdf", "annual leave"), ("git-guide.md", "rebase"), ("wifi.txt", "ninety"),
                    ("ignite-assessment.docx", "three rounds"), ("ignite-onboarding.pptx", "induction")]:
        assert word in " ".join(t for _, t in extract(docs / f)), f
    with pytest.raises(ExtractError):
        extract(docs / "image.png")


def test_folder_ingest_is_incremental_and_skips_unsupported(tmp_path, docs):
    k = KnowledgeBase(tmp_path / "c2", FakeEmbedder())
    r = ingest_path(k, "general", docs, say=lambda m: None)
    assert r["files"] == 5 and len(r["skipped"]) == 1 and not r["errors"]
    again = ingest_path(k, "general", docs, say=lambda m: None)
    assert again["chunks"] == 0                                           # nothing re-embedded
    (docs / "wifi.txt").write_text("The wifi password now rotates every sixty days.")
    assert ingest_path(k, "general", docs / "wifi.txt", say=lambda m: None)["chunks"] == 1
    assert "sixty" in k.query("general", "wifi password rotates", 1)[0].text and "ninety" not in k.query("general", "wifi password rotates", 1)[0].text
    ingest_path(k, "general", docs / "wifi.txt", reset=True, say=lambda m: None)
    assert k.stats()["general"]["sources"] == ["wifi.txt"]


def test_spaces_are_separate(kb):
    assert kb.query("ignite", "annual leave days", 3)[0].source != "leave-policy.pdf"
    assert kb.query("general", "annual leave days", 1)[0].source == "leave-policy.pdf"
    assert kb.stats()["ignite"]["chunks"] >= 2 and kb.stats()["general"]["chunks"] >= 3


def test_routing_order_and_capabilities():
    assert kbrouter.order_for("what is the Ignite assessment process") == ["ignite", "general"]
    assert kbrouter.order_for("how does git rebase work") == ["general", "ignite"]
    policy.set_capability("kb.ignite", False, user_id="u-x")
    try:
        assert kbrouter.allowed_spaces("ignite assessment", "u-x") == ["general"]
    finally:
        policy.set_capability("kb.ignite", True, user_id="u-x")


def test_retriever_finds_right_space_and_falls_back(session, kb):
    r = KBRetriever(kb)
    p = r.retrieve(session, "How many rounds are in the Ignite assessment?")
    assert p and p[0].meta["space"] == "ignite" and "three rounds" in p[0].text
    p = r.retrieve(session, "how many days of annual leave do employees get")                 # no Ignite hint, answer in general
    assert p and p[0].meta["space"] == "general" and p[0].source.startswith("leave-policy.pdf")
    p = r.retrieve(session, "when do trainees receive laptops")                               # hint 'trainee' -> ignite first
    assert p and p[0].meta["space"] == "ignite" and p[0].source.startswith("ignite-onboarding.pptx p.1")
    p = r.retrieve(session, "what is the weather in paris today")
    assert p == []                                                                            # nothing relevant -> nothing


def capture(monkeypatch, reply):
    seen = {"calls": 0}
    def fake(messages, **k):
        seen["calls"] += 1; seen["messages"] = messages
        yield from reply
    monkeypatch.setattr(llm, "chat_stream", fake)
    return seen


def test_strict_chat_refuses_without_calling_the_model(session, kb, monkeypatch):
    seen = capture(monkeypatch, ["should not be used"])
    svc = ChatService(retrievers=[KBRetriever(kb)], strict=True)
    out = "".join(svc.stream_reply(session, "what is the weather in paris today"))
    assert out == prompts.NOT_FOUND and seen["calls"] == 0


def test_strict_chat_answers_from_passages_with_citation_context(session, kb, monkeypatch):
    seen = capture(monkeypatch, ["Three rounds: ", "aptitude, coding, interview [ignite-assessment.docx p.1]."])
    svc = ChatService(retrievers=[KBRetriever(kb)], strict=True)
    out = "".join(svc.stream_reply(session, "How many rounds are in the Ignite assessment?"))
    assert out.startswith("Three rounds") and "[ignite-assessment.docx" in out
    sys, user = seen["messages"][0]["content"], seen["messages"][-1]["content"]
    assert "ONLY from the reference passages" in sys and "ignite-assessment.docx p.1" in user and "three rounds" in user


@pytest.mark.parametrize("reply", [["NOT_IN_CONTEXT"], ["NOT_", "IN_CONTEXT"], ["NOT", "_IN_CONTEXT."]])
def test_model_can_decline_even_with_weak_passages(session, kb, monkeypatch, reply):
    capture(monkeypatch, reply)
    svc = ChatService(retrievers=[KBRetriever(kb)], strict=True)
    assert "".join(svc.stream_reply(session, "How many rounds are in the Ignite assessment?")) == prompts.NOT_FOUND


def test_followup_uses_previous_question_for_retrieval(session, kb, monkeypatch):
    capture(monkeypatch, ["ok [x]"])
    svc = ChatService(retrievers=[KBRetriever(kb)], strict=True)
    session.history += [{"role": "user", "content": "How many rounds are in the Ignite assessment?"}, {"role": "assistant", "content": "Three."}]
    assert "".join(svc.stream_reply(session, "and who conducts it?")) .startswith("ok")


def test_smalltalk_needs_no_kb_or_model():
    from server.domain import router
    assert router.route("hello").kind == "smalltalk" and router.route("thanks!").kind == "smalltalk"
    assert router.route("hello world program in python").kind in ("chat", "browser")


def test_default_service_is_strict_with_kb():
    assert config.RAG_STRICT and "kb" in config.RAG_RETRIEVERS
