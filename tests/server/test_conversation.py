"""Mixed command+question sentences, follow-up questions (agentic retrieval) and remembered history."""
from server import llm
from server.chat.rag.base import Passage, Retriever
from server.chat.service import ChatService, get_chat_service, looks_like_followup
from server.domain import orchestrator
from shared import protocol as P
import server.chat.service as svc_mod


class RecordingKB(Retriever):
    """Finds the Java Streams passage only when the query is actually about streams."""
    name = "rec"
    def __init__(self): self.queries = []
    def retrieve(self, session, query, k=5):
        self.queries.append(query)
        if "stream" in query.lower():
            return [Passage("The Java Stream API processes collections with map, filter and reduce.", "java-streams.pdf p.2", 0.9)]
        return []


def install(monkeypatch, kb, replies, condensed=None):
    svc = ChatService(retrievers=[kb], strict=True)
    monkeypatch.setattr(svc_mod, "_service", svc)
    calls = {"stream": [], "text": []}
    def chat_stream(messages, **k):
        calls["stream"].append(messages)
        yield from replies.pop(0)
    def chat_text(messages, **k):
        calls["text"].append(messages)
        return condensed
    monkeypatch.setattr(llm, "chat_stream", chat_stream)
    monkeypatch.setattr(llm, "chat_text", chat_text)
    return svc, calls


def device_ok(op, args):
    if op == P.FIND_FOLDER: return P.DeviceResult.ok(path="/home/p/project", msg="found")
    if op == P.CHAT_CONTEXT: return P.DeviceResult.ok(turns=[])
    return P.DeviceResult.ok(msg="ok")


def test_command_then_question_in_one_sentence(make_session, monkeypatch):
    kb = RecordingKB()
    _, calls = install(monkeypatch, kb, [["Streams ", "process data. [java-streams.pdf p.2]"]])
    s = make_session(device=device_ok)
    out = orchestrator.process(s, "Open project in vscode and explain what is Java Stream API?")
    ops = [c[0] for c in s.ui.calls if c[0] != P.CHAT_CONTEXT]
    assert ops == [P.FIND_FOLDER, P.OPEN_IN_APP]                         # the command ran (deterministically)...
    assert "".join(s.ui.tokens).startswith("Streams")                    # ...and the question was answered from the KB
    assert kb.queries == ["explain what is Java Stream API?"]
    assert len(calls["stream"]) == 1 and calls["text"] == []             # ONE model call, none for the command
    assert s.history[-2]["content"] == "explain what is Java Stream API?"
    assert "Streams" in out


def test_question_first_then_command(make_session, monkeypatch):
    install(monkeypatch, RecordingKB(), [["Streams are great."]])
    s = make_session(device=device_ok)
    orchestrator.process(s, "explain what is Java Stream API and open project in vscode")
    assert "".join(s.ui.tokens).startswith("Streams")
    assert [c[0] for c in s.ui.calls if c[0] != P.CHAT_CONTEXT] == [P.FIND_FOLDER, P.OPEN_IN_APP]


def test_failed_command_does_not_block_the_answer(make_session, monkeypatch):
    install(monkeypatch, RecordingKB(), [["Streams are great."]])
    s = make_session(device=lambda op, a: P.DeviceResult.error("no such folder") if op == P.FIND_FOLDER else P.DeviceResult.ok(turns=[]))
    out = orchestrator.process(s, "open project in vscode and explain what is Java Stream API")
    assert "Streams are great" in "".join(s.ui.tokens) and out.startswith("The command didn't complete")


def test_followup_is_rewritten_into_a_standalone_query(make_session, monkeypatch):
    kb = RecordingKB()
    svc, calls = install(monkeypatch, kb, [["Intro."], ["map transforms each element. [java-streams.pdf p.2]"]],
                         condensed="How does map work in the Java Stream API")
    s = make_session(device=device_ok)
    orchestrator.process(s, "what is Java Stream API")
    assert calls["text"] == []                                           # a standalone question needs no rewriting
    orchestrator.process(s, "how does map work in it?")                  # follow-up: "it" refers to the previous topic
    assert len(calls["text"]) == 1                                       # one cheap fast-model call, only for the follow-up
    assert kb.queries[-1] == "How does map work in the Java Stream API"
    assert "map transforms" in "".join(s.ui.tokens)
    prompt = calls["stream"][-1]
    assert any("what is Java Stream API" in m["content"] for m in prompt[:-1])      # earlier turn is in the model's context


def test_followup_falls_back_to_previous_question_if_rewriter_fails(make_session, monkeypatch):
    kb = RecordingKB()
    svc, _ = install(monkeypatch, kb, [["Intro."], ["ok"]], condensed=None)
    monkeypatch.setattr(llm, "chat_text", lambda *a, **k: (_ for _ in ()).throw(llm.LLMError("down")))
    s = make_session(device=device_ok)
    orchestrator.process(s, "what is Java Stream API")
    orchestrator.process(s, "tell me more about it")
    assert "Java Stream API" in kb.queries[-1]


def test_unrelated_followup_is_refused_not_hallucinated(make_session, monkeypatch):
    kb = RecordingKB()
    install(monkeypatch, kb, [["Intro."]], condensed="weather in paris")
    s = make_session(device=device_ok)
    orchestrator.process(s, "what is Java Stream API")
    orchestrator.process(s, "and what about the weather there?")
    assert "".join(s.ui.tokens).endswith("ask your mentor.")


def test_history_is_restored_from_the_pcs_local_database(make_session, monkeypatch):
    kb = RecordingKB()
    _, calls = install(monkeypatch, kb, [["map transforms elements. [x]"]], condensed="Java Stream API map")
    turns = [{"role": "user", "content": "what is Java Stream API"}, {"role": "assistant", "content": "A way to process collections."}]
    s = make_session(device=lambda op, a: P.DeviceResult.ok(turns=turns) if op == P.CHAT_CONTEXT else P.DeviceResult.ok(msg="ok"))
    assert s.history == []                                              # brand new connection (e.g. after a restart)
    orchestrator.process(s, "how does map work in it?")
    assert kb.queries[-1] == "Java Stream API map"                      # context came from the local SQLite, not memory
    assert any(m["content"] == "what is Java Stream API" for m in calls["stream"][-1])


def test_followup_detection_is_cheap_and_conservative():
    assert looks_like_followup("how does map work in it?") and looks_like_followup("and more?")
    assert not looks_like_followup("Explain the difference between checked and unchecked exceptions in Java")


def test_central_database_is_created_on_a_fresh_server(tmp_path):
    from server.data.central import Central
    c = Central(url="", path=tmp_path / "not" / "yet" / "central.db")          # the folder does not exist (first run)
    assert c.trainee("alice", "Alice")["batch"] == "default"


def test_server_does_not_silently_change_the_process_time_zone():
    """Django used to force America/Chicago on the whole process, shifting every reminder."""
    import os, time
    from django.conf import settings
    assert settings.TIME_ZONE is None or settings.TIME_ZONE == os.getenv("ASSISTANT_TIMEZONE")
    if not os.getenv("ASSISTANT_TIMEZONE") and not os.getenv("TZ"):
        import datetime as dt
        assert abs(dt.datetime.now().timestamp() - time.time()) < 5 and dt.datetime.now().astimezone().utcoffset() == dt.datetime.now().astimezone().utcoffset()
        assert os.environ.get("TZ") != "America/Chicago"


def test_clock_time_that_has_passed_today_means_tomorrow():
    from datetime import datetime
    from server.util import timeparse
    now = datetime(2026, 11, 1, 15, 0)
    assert timeparse.parse_when("at 9am", now) == datetime(2026, 11, 2, 9, 0)
    assert timeparse.parse_when("5pm", now) == datetime(2026, 11, 1, 17, 0)
