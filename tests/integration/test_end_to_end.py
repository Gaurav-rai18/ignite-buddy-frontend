"""Real server consumer + real client DeviceExecutor over the real wire protocol. Only the OS launcher and the LLM are fake."""
import asyncio
import types
from pathlib import Path

import pytest
from channels.testing import WebsocketCommunicator

from client.device.executor import DeviceExecutor
from client.device.indexer import Index
from server.realtime.consumer import AssistantConsumer


class FakeLauncher:
    def __init__(self): self.log = []
    def open_path(self, p): self.log.append(("open", p))
    def launch_app(self, p): self.log.append(("app", p))
    def which(self, exe): return "/usr/bin/" + exe
    def spawn(self, argv): self.log.append(("spawn", argv))
    def run(self, argv, cwd, timeout): self.log.append(("run", argv, cwd)); return 0, "installed ok"
    def open_url(self, u): self.log.append(("url", u))


@pytest.fixture
def device(tmp_path, monkeypatch):
    monkeypatch.setattr('client.device.executor.SCRIPT_EXT', {'.bat', '.cmd', '.py', '.sh'})   # tests run on any OS
    proj = tmp_path / "Documents" / "react assignment 3"
    proj.mkdir(parents=True)
    (proj / "install.bat").write_text("echo hi\n")
    cfg = types.SimpleNamespace(SEARCH_ROOTS=[tmp_path.resolve()], SCRIPT_ROOTS=[tmp_path.resolve()], SKIP_DIRS=set(),
                                MAX_DEPTH=5, SCRIPT_TIMEOUT=10, DOC_EXTS={".txt"}, MAX_DOC_BYTES=10**6,
                                MAX_DOCS_PER_FOLDER=50, MAX_FILE_BYTES=10**5,
                                WRITE_ROOTS=[tmp_path.resolve()], DEFAULT_PARENT=tmp_path.resolve(), HOME_DIR=tmp_path.resolve() / 'TraineeAssistant')
    idx = Index(cfg.SEARCH_ROOTS, cfg.SKIP_DIRS, 5)
    idx.refresh()
    lau = FakeLauncher()
    confirms = []
    ex = DeviceExecutor(cfg, confirm=lambda t, p: confirms.append((t, p)) or True, launcher=lau, index=idx)
    return ex, lau, confirms, proj


async def connect(token="tokA"):
    comm = WebsocketCommunicator(AssistantConsumer.as_asgi(), "/ws/assistant/")
    ok, _ = await comm.connect()
    assert ok
    await comm.send_json_to({"type": "auth", "token": token, "device_id": "pc1"})
    return comm


async def converse(comm, device_exec, text, replies=None):
    """Send text, serve device calls with the real executor, return (messages, until idle)."""
    await comm.send_json_to({"type": "text", "text": text})
    seen = []
    while True:
        m = await comm.receive_json_from(timeout=15)
        seen.append(m)
        if m["type"] == "device_call":
            res = await asyncio.to_thread(device_exec.handle, m["op"], m["args"])
            await comm.send_json_to({"type": "device_result", "id": m["id"], **res.to_wire()})
        elif m["type"] == "state" and m["state"] == "idle":
            return seen


async def test_bad_token_closed():
    comm = WebsocketCommunicator(AssistantConsumer.as_asgi(), "/ws/assistant/")
    await comm.connect()
    await comm.send_json_to({"type": "auth", "token": "nope"})
    out = await comm.receive_output(timeout=5)
    assert out["type"] == "websocket.close" and out["code"] == 4401


async def test_nothing_works_before_auth():
    comm = WebsocketCommunicator(AssistantConsumer.as_asgi(), "/ws/assistant/")
    await comm.connect()
    await comm.send_json_to({"type": "text", "text": "set a timer for 5 minutes"})
    assert await comm.receive_nothing(timeout=0.5)
    await comm.disconnect()


async def test_compound_command_runs_with_zero_llm_calls(device, monkeypatch):
    ex, lau, confirms, proj = device
    from server import llm
    monkeypatch.setattr(llm, "chat_stream", lambda *a, **k: (_ for _ in ()).throw(AssertionError("LLM was called")))
    comm = await connect()
    assert (await comm.receive_json_from())["type"] == "hello_ok"
    await comm.receive_json_from()                                           # policy
    msgs = await converse(comm, ex, "open the react assignment 3 in vs code and run install.bat")
    types_ = [m["type"] for m in msgs]
    assert types_.count("device_call") == 3
    assert [m["op"] for m in msgs if m["type"] == "device_call"] == ["find_folder", "open_in_app", "run_file"]
    assert ("spawn", ["/usr/bin/code", str(proj)]) in lau.log
    assert any(e[0] == "run" and e[2] == str(proj) for e in lau.log)
    assert confirms and "install.bat" in confirms[0][0]                      # the CLIENT asked the user
    assert any(m["type"] == "speak" and m["text"] == "Done." for m in msgs)
    await comm.disconnect()


async def test_user_declines_script_on_client(device):
    ex, lau, _, _ = device
    ex.confirm = lambda t, p: False
    comm = await connect()
    await comm.receive_json_from(); await comm.receive_json_from()
    msgs = await converse(comm, ex, "run install.bat")
    assert not any(e[0] == "run" for e in lau.log)
    assert any("Cancelled" in m.get("text", "") for m in msgs if m["type"] == "say")
    await comm.disconnect()


async def test_server_side_command_and_user_isolation(device):
    ex, *_ = device
    a, b = await connect("tokA"), await connect("tokB")
    for c in (a, b):
        await c.receive_json_from(); await c.receive_json_from()
    await converse(a, ex, "set a timer for 5 minutes for alice only")
    out_b = await converse(b, ex, "list my timers")
    assert any("No active timers" in m.get("text", "") for m in out_b if m["type"] == "say")
    out_a = await converse(a, ex, "list my timers")
    assert any("alice only" in m.get("text", "") for m in out_a if m["type"] == "say")
    await a.disconnect(); await b.disconnect()


async def test_activity_samples_and_pause_notice(device):
    ex, *_ = device
    comm = await connect()
    await comm.receive_json_from(); await comm.receive_json_from()
    await comm.send_json_to({"type": "activity_sample", "app": "Code", "title": "main.py", "idle": False})
    msgs = await converse(comm, ex, "pause tracking for 30 minutes")
    assert any(m["type"] == "tracking" and m["paused"] for m in msgs)
    await comm.disconnect()


async def test_notes_land_in_the_folder_on_the_device(device):
    ex, lau, _, proj = device
    comm = await connect()
    await comm.receive_json_from(); await comm.receive_json_from()
    msgs = await converse(comm, ex, "note: bring laptop charger to the lab")
    assert any("Saved note" in m.get("text", "") for m in msgs if m["type"] == "say")
    notes = list((ex.vault.notes).glob("*.md"))
    assert len(notes) == 1 and "laptop charger" in notes[0].read_text()
    msgs = await converse(comm, ex, "what did I note about the charger")
    assert any("charger" in m.get("text", "") for m in msgs if m["type"] == "say")
    await comm.disconnect()
