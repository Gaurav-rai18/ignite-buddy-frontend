import asyncio
import json
import types
import pytest
from aiohttp import ClientSession, WSMsgType, web
from aiohttp.test_utils import TestServer

from client.agent.server import Agent
from client.device.executor import DeviceExecutor
from client.device.indexer import Index
from shared import protocol as P


class FakeNet:
    connected = True
    def __init__(self): self.sent, self.audio = [], []
    def send(self, m): self.sent.append(m)
    def send_bytes(self, b): self.audio.append(b)


class L:
    supports_native = False
    def __init__(self): self.log = []
    def open_path(self, p): self.log.append(("open", p))
    def which(self, e): return "/bin/" + e
    def spawn(self, a): self.log.append(("spawn", a))
    def run(self, argv, cwd, timeout): self.log.append(("run", argv)); return 0, "ran"
    def open_url(self, u): self.log.append(("url", u))
    def trash(self, p): self.log.append(("trash", p))


@pytest.fixture
async def rig(tmp_path, monkeypatch):
    monkeypatch.setattr("client.device.executor.SCRIPT_EXT", {".sh", ".bat", ".py"})
    root = tmp_path / "docs"; (root / "proj").mkdir(parents=True); (root / "proj" / "go.sh").write_text("echo hi")
    cfg = types.SimpleNamespace(SEARCH_ROOTS=[root.resolve()], WRITE_ROOTS=[root.resolve()], DEFAULT_PARENT=root.resolve(),
                                HOME_DIR=root.resolve() / "TA", SCRIPT_ROOTS=[root.resolve()], SKIP_DIRS=set(), MAX_DEPTH=4,
                                SCRIPT_TIMEOUT=5, DOC_EXTS={".txt"}, MAX_DOC_BYTES=10**6, MAX_DOCS_PER_FOLDER=5, MAX_FILE_BYTES=10**5)
    idx = Index(cfg.SEARCH_ROOTS, cfg.SKIP_DIRS, 4); idx.refresh()
    lau, net = L(), FakeNet()
    agent = Agent(net, DeviceExecutor(cfg, launcher=lau, index=idx), None, port=0)
    srv = TestServer(agent.build_app())
    await srv.start_server()
    agent.port = srv.port
    agent.loop = asyncio.get_running_loop()
    agent.executor.confirm = agent._confirm_sync
    yield agent, srv, net, lau, root
    await srv.close()


async def open_ui(rig_, token=None, headers=None):
    agent, srv, *_ = rig_
    sess = ClientSession()
    ws = await sess.ws_connect(f"http://127.0.0.1:{srv.port}/ws", headers=headers or {})
    await ws.send_json({"type": "auth", "token": token or agent.token})
    return sess, ws


async def recv(ws, timeout=3):
    m = await ws.receive(timeout=timeout)
    return json.loads(m.data) if m.type == WSMsgType.TEXT else m


async def test_page_embeds_token_and_host_is_checked(rig):
    agent, srv, *_ = rig
    async with ClientSession() as s:
        r = await s.get(f"http://127.0.0.1:{srv.port}/")
        body = await r.text()
        assert r.status == 200 and f'content="{agent.token}"' in body
        assert (await s.get(f"http://127.0.0.1:{srv.port}/", headers={"Host": "evil.example.com"})).status == 403    # DNS rebinding


async def test_ws_needs_token_and_own_origin(rig):
    agent, srv, *_ = rig
    sess, ws = await open_ui(rig, token="wrong")
    m = await ws.receive(timeout=3)
    assert m.type in (WSMsgType.CLOSE, WSMsgType.CLOSED) and ws.close_code == P.CLOSE_UNAUTHORIZED
    await sess.close()
    async with ClientSession() as s:
        with pytest.raises(Exception):
            await s.ws_connect(f"http://127.0.0.1:{srv.port}/ws", headers={"Origin": "https://evil.example.com"})


async def test_ui_messages_are_whitelisted(rig):
    agent, srv, net, *_ = rig
    sess, ws = await open_ui(rig)
    assert (await recv(ws))["type"] == "agent_ready"
    await ws.send_json({"type": "text", "text": "set a timer for 5 minutes"})
    await ws.send_json({"type": "device_result", "id": "r1", "status": "ok"})               # a web page must not fake device results
    await ws.send_json({"type": "capture_response", "id": "r1", "image_b64": "xx"})
    await ws.send_bytes(b"\x00\x01")
    await asyncio.sleep(0.2)
    assert net.sent == [{"type": "text", "text": "set a timer for 5 minutes"}] and net.audio == []     # audio is handled locally, never relayed
    await sess.close()


async def test_server_messages_reach_the_ui(rig):
    agent, srv, net, *_ = rig
    sess, ws = await open_ui(rig)
    await recv(ws)
    await agent.on_server_msg({"type": "token", "text": "Hi"})
    await agent.on_server_msg({"type": "_disconnected", "code": 4401})
    assert (await recv(ws)) == {"type": "token", "text": "Hi"}
    link = await recv(ws)
    assert link["type"] == "link" and link["status"] == "auth_failed" and link["connected"] is False and link["auth_failed"] is True
    await sess.close()


async def test_device_call_runs_python_on_the_pc(rig):
    agent, srv, net, lau, root = rig
    await agent.on_server_msg({"type": "device_call", "id": "r9", "op": "create_folder", "args": {"name": "from-react"}})
    for _ in range(40):
        if net.sent: break
        await asyncio.sleep(0.05)
    assert (root / "from-react").is_dir()
    assert net.sent[0]["type"] == "device_result" and net.sent[0]["id"] == "r9" and net.sent[0]["status"] == P.OK


async def test_run_script_needs_a_click_in_the_ui(rig):
    agent, srv, net, lau, root = rig
    sess, ws = await open_ui(rig)
    await recv(ws)
    call = {"type": "device_call", "id": "r1", "op": "run_file", "args": {"file": "go.sh", "cwd": str(root / "proj")}}
    await agent.on_server_msg(call)
    ask = await recv(ws)
    assert ask["type"] == "local_confirm" and "go.sh" in ask["title"] and "echo hi" in ask["preview"]
    await ws.send_json({"type": "local_confirm_response", "id": ask["id"], "approved": True})
    for _ in range(40):
        if net.sent: break
        await asyncio.sleep(0.05)
    assert net.sent[-1]["status"] == P.OK and any(x[0] == "run" for x in lau.log)

    lau.log.clear(); net.sent.clear()
    await agent.on_server_msg({**call, "id": "r2"})
    ask = await recv(ws)
    await ws.send_json({"type": "local_confirm_response", "id": ask["id"], "approved": False})
    for _ in range(40):
        if net.sent: break
        await asyncio.sleep(0.05)
    assert net.sent[-1]["status"] == P.CANCELLED and not lau.log
    await sess.close()


async def test_no_ui_means_no_script(rig):
    agent, srv, net, lau, root = rig
    await agent.on_server_msg({"type": "device_call", "id": "r1", "op": "run_file", "args": {"file": "go.sh", "cwd": str(root / "proj")}})
    for _ in range(60):
        if net.sent: break
        await asyncio.sleep(0.05)
    assert net.sent[-1]["status"] == P.CANCELLED and not lau.log


async def test_screenshot_is_only_sent_after_preview_approval(rig, monkeypatch):
    agent, srv, net, *_ = rig
    from client.device import capture
    monkeypatch.setattr(capture, "capture_payload", lambda: {"image_b64": "AAAA", "app": "Code", "title": "main.py"})
    sess, ws = await open_ui(rig)
    await recv(ws)
    await agent.on_server_msg({"type": "capture_request", "id": "c1"})
    prev = await recv(ws)
    assert prev["type"] == "capture_preview" and prev["image_b64"] == "AAAA" and not net.sent
    await ws.send_json({"type": "capture_decision", "id": prev["id"], "approved": False})
    await asyncio.sleep(0.2)
    assert net.sent[-1] == {"type": "capture_response", "id": "c1", "image_b64": None}
    await agent.on_server_msg({"type": "capture_request", "id": "c2"})
    prev = await recv(ws)
    await ws.send_json({"type": "capture_decision", "id": prev["id"], "approved": True, "include_file": True})
    await asyncio.sleep(0.2)
    assert net.sent[-1]["image_b64"] == "AAAA" and net.sent[-1]["include_file"] is True
    await sess.close()


async def test_late_ui_gets_state_the_server_already_sent(rig):
    agent, srv, net, *_ = rig
    await agent.on_server_msg({"type": "_connected"})
    await agent.on_server_msg({"type": "hello_ok", "user": {"id": "alice", "name": "alice"}, "capabilities": {"files.delete": False}})
    await agent.on_server_msg({"type": "policy", "blocked": False, "reason": ""})
    sess, ws = await open_ui(rig)                          # page opens AFTER all of that happened
    ready = await recv(ws)
    assert ready["type"] == "agent_ready" and ready["status"] == "ready" and ready["connected"] is True
    assert (await recv(ws))["type"] == "hello_ok" and (await recv(ws))["type"] == "policy"
    await sess.close()


async def test_socket_open_is_not_ready_until_the_server_accepts_the_login(rig):
    agent, *_ = rig
    await agent.on_server_msg({"type": "_connected"})
    assert agent.status == "authenticating" and agent.link_msg()["connected"] is False
    await agent.on_server_msg({"type": "hello_ok", "user": {"name": "a"}})
    assert agent.status == "ready"


async def test_failure_reasons_reach_the_ui(rig, capsys):
    agent, srv, *_ = rig
    sess, ws = await open_ui(rig)
    await recv(ws)
    await agent.on_server_msg({"type": "_error", "error": "SSLCertVerificationError: unable to get local issuer certificate"})
    msg = await recv(ws)
    assert msg["status"] == "unreachable" and "SSLCertVerificationError" in msg["detail"] and msg["server"]
    await agent.on_server_msg({"type": "_disconnected", "code": 4401})
    assert (await recv(ws))["status"] == "auth_failed"
    assert "server link: auth_failed" in capsys.readouterr().out                   # also printed in the agent's console
    await sess.close()


async def test_sampler_waits_for_ready(rig):
    agent, *_ = rig
    agent.sampler = types.SimpleNamespace(connected=False, blocked=False, set_tracking=lambda *a: None)
    await agent.on_server_msg({"type": "_connected"})
    assert agent.sampler.connected is False
    await agent.on_server_msg({"type": "hello_ok", "user": {"name": "a"}})
    assert agent.sampler.connected is True
    await agent.on_server_msg({"type": "_disconnected", "code": 1006})
    assert agent.sampler.connected is False


def test_network_errors_are_explained():
    from client.agent.server import explain
    url = "ws://server:8765/ws/assistant/"
    t = explain("TimeoutError: [WinError 10060] A connection attempt failed", url)
    assert "server:8765" in t and "ASSISTANT_HOST=0.0.0.0" in t and "placeholder" in t
    assert "cannot be resolved" in explain("gaierror: [Errno 11001] getaddrinfo failed", url)
    assert "nothing is listening" in explain("ConnectionRefusedError: [WinError 10061]", url)
    assert "TLS" in explain("SSLCertVerificationError: unable to get local issuer", "wss://x/ws")
    assert explain("something odd", url) == ""


async def test_unreachable_detail_contains_the_hint(rig):
    agent, *_ = rig
    agent.net.url = "ws://server:8765/ws/assistant/"
    await agent.on_server_msg({"type": "_error", "error": "TimeoutError: [WinError 10060] no response"})
    assert agent.status == "unreachable" and "ASSISTANT_HOST=0.0.0.0" in agent.detail


# ---------------- local memory, audit and admin sync in the agent ----------------
async def test_agent_remembers_answered_turns_but_not_refusals_or_commands(rig, tmp_path):
    from client.localdb import LocalDB
    agent, srv, net, *_ = rig
    agent.db = LocalDB(tmp_path / "mem.db")
    sess, ws = await open_ui(rig)
    await recv(ws)
    await ws.send_json({"type": "text", "text": "what is Java Stream API"})
    await asyncio.sleep(0.1)
    for chunk in ("Streams process ", "collections."):
        await agent.on_server_msg({"type": "token", "text": chunk})
    await agent.on_server_msg({"type": "message_end"})
    await ws.send_json({"type": "text", "text": "weather in paris"})
    await asyncio.sleep(0.1)
    await agent.on_server_msg({"type": "token", "text": P.REFUSAL_PREFIX + " I couldn't find anything."})
    await agent.on_server_msg({"type": "message_end"})
    await ws.send_json({"type": "text", "text": "set a timer for 5 minutes"})          # a command: no tokens, nothing stored
    await asyncio.sleep(0.1)
    await agent.on_server_msg({"type": "message_end"})
    assert agent.db.chat_context("") == [{"role": "user", "content": "what is Java Stream API"},
                                         {"role": "assistant", "content": "Streams process collections."}]
    await sess.close()


async def test_agent_applies_admin_sync_and_notifies(rig, tmp_path):
    from client.localdb import LocalDB
    agent, srv, net, *_ = rig
    agent.db = LocalDB(tmp_path / "sync.db")
    sess, ws = await open_ui(rig)
    await recv(ws)
    await agent.on_server_msg({"type": "sync", "cursor": 7, "assignments": [{"id": "a1", "title": "React app", "due_ts": 1.9e9}],
                               "timetable": [{"id": "t1", "weekday": 0, "start": "09:00", "end": "10:00", "title": "Java"}]})
    note = await recv(ws)
    assert note["type"] == "notification" and "New assignment: React app" in note["text"] and "timetable" in note["text"]
    assert agent.db.cursor() == 7 and agent.db.assignments()[0][1] == "React app"
    await sess.close()


def test_local_commands_and_audit_never_store_content(tmp_path):
    from client.localdb import LocalDB
    db = LocalDB(tmp_path / "a.db")
    db.audit("add_note", {"text": "my secret diary"}, "ok")
    db.audit("create_folder", {"name": "react"}, "ok")
    rows = db.recent_audit()
    assert all("diary" not in r[2] for r in rows) and any("name=react" in r[2] for r in rows)
    db.add_chat("Q1 java streams", "A1")
    for i in range(10):
        db.add_chat(f"unrelated question {i}", "x")
    ctx = db.chat_context("java streams again")                         # older but RELEVANT turn is pulled back in
    assert any(m["content"] == "Q1 java streams" for m in ctx)


async def test_shell_messages_only_reach_a_shell_and_config_is_sent(rig, tmp_path, monkeypatch):
    agent, srv, net, *_ = rig
    glb = tmp_path / "me.glb"; glb.write_bytes(b"glTF-fake")
    monkeypatch.setattr("client.config.AVATAR_GLB", str(glb))
    got = []
    sess, ws = await open_ui(rig)
    ready = await recv(ws)
    assert ready["config"]["stt"] and ready["config"]["hotkey"]
    await ws.send_json({"type": "shell_hit", "rects": [[0, 0, 10, 10]]})                  # no shell attached: ignored
    await asyncio.sleep(0.2)
    agent.shell = got.append
    await ws.send_json({"type": "shell_hit", "rects": [[0, 0, 10, 10]]})
    await ws.send_json({"type": "shell_quit"})
    await ws.send_json({"type": "text_evil_unknown", "x": 1})
    await asyncio.sleep(0.2)
    assert [m["type"] for m in got] == ["shell_hit", "shell_quit"] and net.sent == []
    agent.push_shell("activate")
    assert (await recv(ws)) == {"type": "shell", "action": "activate"}
    async with ClientSession() as s:
        r = await s.get(f"http://127.0.0.1:{srv.port}/avatar.glb")
        assert r.status == 200 and (await r.read()) == b"glTF-fake"
    await sess.close()


async def test_start_server_falls_back_to_a_free_port(tmp_path):
    import socket
    from client.agent.server import Agent
    busy = socket.socket(); busy.bind(("127.0.0.1", 0)); busy.listen(); port = busy.getsockname()[1]
    agent = Agent(FakeNet(), types.SimpleNamespace(confirm=None, db=None), None, port=port)
    agent.loop = asyncio.get_running_loop()
    url = await agent.start_server()
    assert url.startswith("http://127.0.0.1:") and agent.port != port
    await agent.runner.cleanup(); busy.close()


# ---------------- speech: recognised on the PC with SpeechRecognition; the server only gets text ----------------
class FakeTranscriber:
    def __init__(self, text="open task manager", error=None): self.text, self.error, self.calls = text, error, []
    def transcribe(self, pcm):
        self.calls.append(len(pcm))
        if self.error: raise self.error
        return self.text


AUDIO = b"\x01\x02" * 16000                                                # 1 s


async def speak(ws, agent, frames=2):
    await ws.send_json({"type": "audio_start"})
    await asyncio.sleep(0.05)
    for _ in range(frames):
        await ws.send_bytes(AUDIO)
    await asyncio.sleep(0.05)
    await ws.send_json({"type": "audio_end"})


async def test_audio_forwarded_to_server_in_one_shot(rig):
    agent, srv, net, *_ = rig
    sess, ws = await open_ui(rig)
    await recv(ws)
    await ws.send_bytes(AUDIO)
    await asyncio.sleep(0.05)
    assert len(net.sent) >= 1
    assert net.sent[-1]["type"] == "audio"
    assert "data" in net.sent[-1]
    assert net.audio == [AUDIO]
    await sess.close()


async def test_mic_controls_handled(rig):
    agent, srv, net, *_ = rig
    sess, ws = await open_ui(rig)
    await recv(ws)
    await ws.send_json({"type": "mic_start"})
    await asyncio.sleep(0.05)
    await ws.send_json({"type": "mic_cancel"})
    await asyncio.sleep(0.05)
    await sess.close()
