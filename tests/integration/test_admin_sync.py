"""Admin API -> central database -> live push -> trainee PC (local SQLite) -> deterministic answers. Real consumer, real executor."""
import asyncio
import json
import types
import uuid

import pytest
from channels.testing import WebsocketCommunicator
from django.test import AsyncClient

from client.device.executor import DeviceExecutor
from client.device.indexer import Index
from client.localdb import LocalDB
from server.data.central import get_central
from server.realtime.consumer import AssistantConsumer

H = {"headers": {"X-Admin-Token": "admin-secret"}}


def mk_executor(tmp_path):
    cfg = types.SimpleNamespace(SEARCH_ROOTS=[tmp_path], WRITE_ROOTS=[tmp_path], DEFAULT_PARENT=tmp_path, HOME_DIR=tmp_path / "TA",
                                SCRIPT_ROOTS=[tmp_path], SKIP_DIRS=set(), MAX_DEPTH=3, SCRIPT_TIMEOUT=5, DOC_EXTS={".txt"},
                                MAX_DOC_BYTES=10**6, MAX_DOCS_PER_FOLDER=5, MAX_FILE_BYTES=10**5, LOCAL_DB=tmp_path / "pc.db")
    return DeviceExecutor(cfg, index=Index([tmp_path], set(), 3), db=LocalDB(tmp_path / "pc.db"))


async def login(token="tokA", cursor=0):
    comm = WebsocketCommunicator(AssistantConsumer.as_asgi(), "/ws/assistant/")
    await comm.connect()
    await comm.send_json_to({"type": "auth", "token": token, "device_id": "pc", "sync_cursor": cursor})
    return comm


async def drain(comm, until, timeout=10):
    seen = []
    while True:
        m = await comm.receive_json_from(timeout=timeout)
        seen.append(m)
        if until(m):
            return seen


async def ask(comm, ex, text):
    await comm.send_json_to({"type": "text", "text": text})
    out = []
    while True:
        m = await comm.receive_json_from(timeout=15)
        out.append(m)
        if m["type"] == "device_call":
            res = await asyncio.to_thread(ex.handle, m["op"], m["args"])
            await comm.send_json_to({"type": "device_result", "id": m["id"], **res.to_wire()})
        if m["type"] == "state" and m["state"] == "idle":
            return " ".join(x.get("text", "") for x in out if x["type"] == "say")


async def test_admin_api_requires_the_token():
    c = AsyncClient()
    assert (await c.get("/admin-api/assignments")).status_code == 403
    assert (await c.get("/admin-api/assignments", headers={"X-Admin-Token": "wrong"})).status_code == 403
    assert (await c.get("/admin-api/assignments", **H)).status_code == 200


async def test_publish_while_online_reaches_the_pc_and_commands_answer_from_local_sqlite(tmp_path):
    batch = "b" + uuid.uuid4().hex[:6]
    ex = mk_executor(tmp_path)
    comm = await login()
    await drain(comm, lambda m: m["type"] == "policy")
    await asyncio.to_thread(get_central().trainee, "alice", "alice")
    await asyncio.to_thread(get_central().set_batch, "alice", batch)       # admin moves alice into a batch...
    comm2 = await login()                                                  # ...and she logs in again (new connection joins that batch)
    await drain(comm2, lambda m: m["type"] == "policy")
    api = AsyncClient()
    r = await api.post("/admin-api/assignments", json.dumps({"batch": batch, "title": "React todo app", "description": "Use hooks",
                                                              "due": "2030-01-05T17:00"}), content_type="application/json", **H)
    assert r.status_code == 201
    r = await api.post("/admin-api/timetable", json.dumps({"batch": batch, "weekday": 0, "start": "09:30", "end": "11:00",
                                                            "title": "Java Streams", "location": "Lab 2"}), content_type="application/json", **H)
    assert r.status_code == 201
    msg = {"assignments": [], "timetable": [], "cursor": 0}
    while not (msg["assignments"] and msg["timetable"]):                    # two publishes -> two live pushes
        got = (await drain(comm2, lambda m: m["type"] == "sync"))[-1]
        msg = {"assignments": msg["assignments"] + got["assignments"], "timetable": msg["timetable"] + got["timetable"],
               "cursor": got["cursor"]}
    assert [a["title"] for a in msg["assignments"]] == ["React todo app"] and msg["timetable"][0]["title"] == "Java Streams"
    ex.db.apply_sync(msg)                                                  # what the agent does
    assert ex.db.cursor() == msg["cursor"]
    assert "React todo app" in await ask(comm2, ex, "what assignments are due")
    assert "Java Streams" in await ask(comm2, ex, "show my timetable for monday")
    assert "Marked 'React todo app' as done" in await ask(comm2, ex, "I submitted the react assignment")
    assert "No pending" in await ask(comm2, ex, "show my pending assignments")
    await comm.disconnect(); await comm2.disconnect()


async def test_offline_pc_catches_up_by_cursor_and_sees_deletions(tmp_path):
    batch = "c" + uuid.uuid4().hex[:6]
    central = get_central()
    await asyncio.to_thread(central.trainee, "bob", "bob")
    await asyncio.to_thread(central.set_batch, "bob", batch)
    a1 = central.upsert_assignment(batch, "Old one", "", 1.9e9)
    comm = await login("tokB", cursor=0)
    got = await drain(comm, lambda m: m["type"] == "sync")
    first = got[-1]
    assert [a["id"] for a in first["assignments"]] == [a1]
    await comm.disconnect()
    central.delete_assignment(a1)                                          # PC is offline while the admin deletes + adds
    a2 = central.upsert_assignment(batch, "New one", "", 1.9e9)
    comm = await login("tokB", cursor=first["cursor"])                     # reconnect with the saved cursor: only the delta
    got = await drain(comm, lambda m: m["type"] == "sync")
    delta = got[-1]
    assert {a["id"]: a["deleted"] for a in delta["assignments"]} == {a1: True, a2: False}
    db = LocalDB(tmp_path / "x.db")
    db.apply_sync(first); changed = db.apply_sync(delta)
    assert [r[1] for r in db.assignments()] == ["New one"] and changed["removed"] == 1
    await comm.disconnect()


async def test_other_batches_do_not_see_it(tmp_path):
    central = get_central()
    await asyncio.to_thread(central.trainee, "alice", "alice")
    await asyncio.to_thread(central.set_batch, "alice", "team-x" + uuid.uuid4().hex[:4])
    central.upsert_assignment("someone-elses-batch", "Secret task", "", 1.9e9)
    comm = await login("tokA", cursor=10**9)
    await drain(comm, lambda m: m["type"] == "policy")
    assert await comm.receive_nothing(timeout=0.5)
    await comm.disconnect()


async def test_admin_panel_page_is_served():
    r = await AsyncClient().get("/admin/")
    body = r.content.decode()
    assert r.status_code == 200 and "Admin panel" in body and "/admin-api/" in body and r.headers["X-Frame-Options"] == "DENY"
