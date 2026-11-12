"""
Local agent: the "Python that executes commands on the PC" for the React frontend (no Electron needed).

    React page (browser)  <--ws://127.0.0.1:8777/ws-->  this agent  <--wss-->  central server
                                                          |
                                                          +-- DeviceExecutor: open apps, find/create files, notes, scripts...
                                                          +-- activity sampler, screenshot capture, file index

The agent serves the built React app itself (same origin => no CORS) and binds to 127.0.0.1 only. Because any web page
open in the same browser could try to reach localhost, the agent defends itself:
  * Host header must be 127.0.0.1/localhost (blocks DNS rebinding)      * WebSocket Origin must be the agent's own origin
  * a random per-run token is embedded in the served page and must be the first WebSocket message
  * the UI may only send a short whitelist of message types; it can NOT inject device results or server replies
  * device operations still go through DeviceExecutor's allowlists, and risky ones (run script, delete) need a click
    in the UI (`local_confirm`) before anything happens
"""
import argparse
import asyncio
import base64
import itertools
import json
import secrets
import shutil
import threading
import time
import webbrowser
from pathlib import Path

from aiohttp import WSMsgType, web

from client import config
from client.localdb import LocalDB
from shared import protocol as P

STATIC = Path(__file__).parent / "static"
UI_TO_SHELL = {"shell_hit", "shell_hide", "shell_quit", "shell_active"}          # window control for the PySide6 desktop shell (ignored in a plain browser)
UI_TO_SERVER = {"text", "audio", "cancel", "settings", "confirm_response", "choose_response", "dev_set_blocked", "ping",
                "assignments_get", "assignment_submit"}   # assignment list/submission relayed to the central server
UI_LOCAL_MIC = {"mic_start", "mic_stop", "mic_cancel"}                           # local mic capture forwarded to backend STT
AUTH_TIMEOUT = 5.0
FALLBACK = "<h3>Trainee Assistant agent is running, but the React UI is not built.</h3><p>Run <code>npm install && npm run build</code> in <code>frontend/</code>.</p>"


def explain(error: str, url: str) -> str:
    """Turn a raw socket error into what the person should check."""
    from urllib.parse import urlparse
    u = urlparse(url)
    where = f"{u.hostname}:{u.port or (443 if u.scheme == 'wss' else 80)}"
    e = error.lower()
    if "10060" in e or "timed out" in e or "timeouterror" in e:
        return (f"no response from {where}. Check: the host name/IP is the REAL server (not the README placeholder 'server'); "
                "the server is running and started with ASSISTANT_HOST=0.0.0.0 (default is this-machine-only); "
                "a firewall/VPN is not blocking the port.")
    if "11001" in e or "getaddrinfo" in e or "name or service not known" in e or "nodename" in e:
        return f"the name '{u.hostname}' cannot be resolved. Use the server's real host name or IP address in ASSISTANT_URL."
    if "10061" in e or "refused" in e:
        return f"{where} answered but nothing is listening there. Start trainee-server, and check the port number."
    if "ssl" in e or "certificate" in e:
        return "TLS certificate problem. Use the correct wss:// host name, or install the company root certificate."
    if "407" in e or "proxy" in e:
        return "a proxy is in the way. Set HTTPS_PROXY/NO_PROXY for this shell, or ask IT to allow the server."
    return ""


class Agent:
    def __init__(self, net, executor, sampler=None, port=8777):
        self.net, self.executor, self.sampler, self.port = net, executor, sampler, port
        self.token = secrets.token_urlsafe(24)
        # What the UI needs to know, kept HERE so a page that opens (or reloads) later still sees it.
        # status: connecting -> authenticating (socket open, login not yet accepted) -> ready | auth_failed | unreachable
        if not getattr(net, "token", ""):
            self.status, self.detail = "auth_failed", "no token configured"
        else:
            self.status, self.detail = "connecting", ""
        self.cache: dict[str, dict] = {}                 # latest hello_ok / policy / tracking from the server
        self.shell = None                                 # callable(msg) set by the desktop shell
        self.ui_config = {"stt": config.STT_ENGINE, "lang": config.SPEECH_LANG, "hotkey": config.HOTKEY,
                          "avatar": bool(config.AVATAR_GLB) and Path(config.AVATAR_GLB).is_file(), "shell": False}
        self.db: LocalDB = getattr(executor, "db", None) or LocalDB(config.LOCAL_DB)
        self._q, self._reply = "", []                    # the turn being streamed: remembered locally when it completes
        if getattr(net, "auth_extra", "x") is None:
            net.auth_extra = lambda: {"sync_cursor": self.db.cursor()}     # ask the server only for what changed
        self.uis: set[web.WebSocketResponse] = set()
        self._pending: dict[str, asyncio.Future] = {}
        self._ids = itertools.count(1)
        self.loop: asyncio.AbstractEventLoop | None = None
        self._listener = None
        executor.confirm = self._confirm_sync                       # risky device ops ask the person in the UI

    # ------------------------------------------------------------------ helpers
    @property
    def origins(self):
        return {f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"}

    async def broadcast(self, msg: dict):
        for ws in list(self.uis):
            try:
                await ws.send_json(msg)
            except Exception:
                self.uis.discard(ws)

    async def ask_ui(self, kind: str, payload: dict, timeout: float = 300):
        """Send a question to the UI and wait for its answer ({} if nobody answers)."""
        if not self.uis:
            return {}
        rid = f"a{next(self._ids)}"
        fut = self.loop.create_future()
        self._pending[rid] = fut
        await self.broadcast({"type": kind, "id": rid, **payload})
        try:
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            return {}
        finally:
            self._pending.pop(rid, None)

    def _confirm_sync(self, title: str, preview: str) -> bool:
        """Called from DeviceExecutor's worker thread."""
        if not self.loop:
            return False
        fut = asyncio.run_coroutine_threadsafe(self.ask_ui("local_confirm", {"title": title, "preview": preview}), self.loop)
        try:
            return bool(fut.result(timeout=320).get("approved"))
        except Exception:
            return False

    def link_msg(self) -> dict:
        return {"type": "link", "status": self.status, "connected": self.status == "ready",
                "auth_failed": self.status == "auth_failed", "detail": self.detail,
                "server": getattr(self.net, "url", config.SERVER_URL)}

    def _set_status(self, status: str, detail: str = ""):
        if (status, detail) != (self.status, self.detail):
            print(f"[agent] server link: {status}" + (f" ({detail})" if detail else ""), flush=True)
        self.status, self.detail = status, detail
        if self.sampler:
            self.sampler.connected = status == "ready"      # nothing is sampled until the server accepted the login

    # ------------------------------------------------------------------ central server -> UI / device
    async def on_server_msg(self, m: dict):
        t = m.get("type")
        if t == "_connected":
            self._set_status("authenticating")
            await self.broadcast(self.link_msg())
        elif t == "_error":
            if self.status != "ready":
                err = m.get("error", "")
                hint = explain(err, getattr(self.net, "url", config.SERVER_URL))
                self._set_status("unreachable", f"{err.split(': ', 1)[0]} -> {hint}" if hint else err)
            await self.broadcast(self.link_msg())
        elif t == "_disconnected":
            self.cache.clear()
            if m.get("code") == P.CLOSE_UNAUTHORIZED:
                self._set_status("auth_failed", "the server rejected ASSISTANT_TOKEN")
            else:
                self._set_status("unreachable", self.detail if self.status == "unreachable" else "connection closed")
            await self.broadcast(self.link_msg())
        elif t == "sync":
            await self._apply_sync(m)
        elif t == "device_call":
            asyncio.create_task(self._device(m))
        elif t == "capture_request":
            asyncio.create_task(self._capture(m))
        else:
            self._record(m)
            if t in ("hello_ok", "policy", "tracking"):
                self.cache[t] = m
            if t == "tracking" and self.sampler:
                self.sampler.set_tracking(bool(m.get("paused")), m.get("seconds"))
            elif t == "policy" and self.sampler:
                self.sampler.blocked = bool(m.get("blocked"))
            elif t == "hello_ok":
                self._set_status("ready")
                if self.sampler:
                    tr = m.get("tracking") or {}
                    self.sampler.set_tracking(bool(tr.get("paused")), tr.get("seconds"))
                meta = m.get("trainee_meta")
                if isinstance(meta, dict) and meta and self.db:
                    for k, v in meta.items():
                        if v is not None:
                            self.db.set_meta(k, str(v))
                asyncio.create_task(self._send_schedule_data())
            await self.broadcast(m)
            if t == "hello_ok":
                await self.broadcast(self.link_msg())

    # ---- local memory: relevant Q&A turns are kept in the PC's SQLite database ----
    def _record(self, m: dict):
        t = m.get("type")
        if t == "transcript" and m.get("final") and m.get("text"):
            self._q, self._reply = m["text"], []
        elif t == "token":
            self._reply.append(m.get("text", ""))
        elif t == "message_end":
            answer = "".join(self._reply).strip()
            q, self._q, self._reply = self._q, "", []
            if q and answer and not q.startswith("/") and not answer.startswith(P.REFUSAL_PREFIX):
                try:
                    self.db.add_chat(q, answer)
                except Exception:
                    pass

    async def _apply_sync(self, m: dict):
        """Assignments / timetable published by the admin panel."""
        try:
            changed = await asyncio.to_thread(self.db.apply_sync, m)
        except Exception as e:
            print(f"[agent] sync failed: {type(e).__name__}: {e}", flush=True)
            return
        bits = []
        if changed["new"]:
            bits.append("New assignment: " + ", ".join(changed["new"]))
        if changed["updated"]:
            bits.append("Updated: " + ", ".join(changed["updated"]))
        if changed["slots"]:
            bits.append("Your timetable was updated")
            await self._send_schedule_data()
        if bits:
            await self.broadcast({"type": "notification", "kind": "assignment", "text": ". ".join(bits) + "."})

    async def _device(self, m: dict):
        op = str(m.get("op", ""))
        res = await asyncio.to_thread(self.executor.handle, op, m.get("args", {}))
        self.net.send({"type": "device_result", "id": m.get("id"), **res.to_wire()})
        if op == "list_folder" and res.status == "ok":
            await self.broadcast({
                "type": "folder_listing",
                "folder": res.data.get("folder", ""),
                "path": res.data.get("path", ""),
                "parent_path": res.data.get("parent_path"),
                "items": res.data.get("items", []),
                "recursive_items": res.data.get("recursive_items", []),
            })
        if op == P.SHOW_TIMETABLE:
            await self._send_schedule_data(open_tab=True)
            await self.broadcast({"type": "set_tab", "tab": "schedule"})
        elif op == P.NEXT_CLASS:
            await self._send_schedule_data(open_tab=False)
        if any(w in op for w in ("task", "note")):
            await self._send_vault_data()

    async def _capture(self, m: dict):
        rid = m.get("id")
        try:
            from client.device import capture
            payload = await asyncio.to_thread(capture.capture_payload)
        except Exception as e:
            await self.broadcast({"type": "say", "text": f"Screenshots are not available on this computer ({type(e).__name__})."})
            self.net.send({"type": "capture_response", "id": rid, "image_b64": None})
            return
        decision = await self.ask_ui("capture_preview", payload)          # the person sees the image BEFORE it leaves
        if decision.get("approved"):
            self.net.send({"type": "capture_response", "id": rid, **payload, "include_file": bool(decision.get("include_file"))})
        else:
            self.net.send({"type": "capture_response", "id": rid, "image_b64": None})

    # ------------------------------------------------------------------ HTTP / WebSocket
    @web.middleware
    async def _guard(self, request, handler):
        host = request.headers.get("Host", "")
        if host not in (f"127.0.0.1:{self.port}", f"localhost:{self.port}"):
            raise web.HTTPForbidden(text="bad host")
        return await handler(request)

    async def index(self, request):
        page = STATIC / "index.html"
        html = page.read_text(encoding="utf-8") if page.exists() else f"<html><head></head><body>{FALLBACK}</body></html>"
        html = html.replace("</head>", f'<meta name="agent-token" content="{self.token}"></head>', 1)
        return web.Response(text=html, content_type="text/html", headers={"Cache-Control": "no-store", "X-Frame-Options": "DENY"})

    async def ws(self, request):
        origin = request.headers.get("Origin")
        if origin is not None and origin not in self.origins:
            raise web.HTTPForbidden(text="bad origin")
        sock = web.WebSocketResponse(heartbeat=20, max_msg_size=P.MAX_SCREENSHOT_BYTES * 2)
        await sock.prepare(request)
        try:
            first = await sock.receive(timeout=AUTH_TIMEOUT)
            msg = json.loads(first.data) if first.type == WSMsgType.TEXT else {}
        except (asyncio.TimeoutError, ValueError):
            msg = {}
        if msg.get("type") != "auth" or not secrets.compare_digest(str(msg.get("token", "")), self.token):
            await sock.close(code=P.CLOSE_UNAUTHORIZED)
            return sock
        self.uis.add(sock)
        # a page that opens late must not miss what the server already told the agent
        await sock.send_json({"type": "agent_ready", "version": P.PROTOCOL_VERSION, "config": self.ui_config,
                              **{k: v for k, v in self.link_msg().items() if k != "type"}})
        for kind in ("hello_ok", "policy", "tracking"):
            if kind in self.cache:
                await sock.send_json(self.cache[kind])
        await self._send_vault_data(sock)
        await self._send_schedule_data(sock)
        try:
            async for frame in sock:
                if frame.type == WSMsgType.BINARY:
                    # Audio is not processed on the client PC; forward in one shot to the backend server
                    self.net.send({"type": "audio", "data": base64.b64encode(frame.data).decode("ascii")})
                    if hasattr(self.net, "send_bytes"):
                        self.net.send_bytes(frame.data)
                elif frame.type == WSMsgType.TEXT:
                    await self._from_ui(frame.data)
        finally:
            self.uis.discard(sock)
            if not self.uis and self._listener and self._listener.active:
                self._listener.cancel()
        return sock

    async def _from_ui(self, data: str):
        try:
            m = json.loads(data)
            t = m["type"]
        except (ValueError, KeyError, TypeError):
            return
        if t in UI_LOCAL_MIC:
            if t == "mic_start":
                self._start_mic()
            elif t == "mic_stop":
                self._stop_mic()
            elif t == "mic_cancel":
                self._cancel_mic()
        elif t == "audio":
            self.net.send(m)
        elif t == "login":
            # Desktop login: exchange user_id+password for JWT, reconnect WS with it.
            asyncio.create_task(self._handle_login(m.get("user_id", ""), m.get("password", ""), m.get("new_password", "")))
        elif t == "logout":
            config.clear_token()
            self.net.token = ""
            self.net._auth_failed = True
            if self.net.ws:
                try:
                    self.net.ws.close()
                except Exception:
                    pass
            print("[agent] Trainee signed out. Session token cleared.")
            await self.broadcast({"type": "auth_state", "authenticated": False})
        elif t in UI_TO_SERVER:
            if t == "text":
                self._q, self._reply = str(m.get("text", "")), []
            self.net.send(m)
        elif t in UI_TO_SHELL:
            if self.shell:
                self.shell(m)
        elif t == "vault_get":
            await self._send_vault_data()
        elif t == "schedule_get":
            await self._send_schedule_data()
            if self.net and self.net.connected:
                force = len(self.db.slots()) == 0 if self.db else False
                self.net.send({"type": "sync_request", "sync_cursor": 0 if force else (self.db.cursor() if self.db else 0), "force": force})
        elif t == "task_mutate":
            action = m.get("action")
            vault = self.executor.vault
            items = vault._load()
            if action == "add":
                txt = str(m.get("text", "")).strip()
                if txt:
                    items.append([False, txt])
                    vault._save(items)
            elif action == "toggle":
                idx = int(m.get("index", -1))
                if 0 <= idx < len(items):
                    items[idx][0] = not items[idx][0]
                    vault._save(items)
            elif action == "delete":
                idx = int(m.get("index", -1))
                if 0 <= idx < len(items):
                    items.pop(idx)
                    vault._save(items)
            await self._send_vault_data()
        elif t == "note_mutate":
            action = m.get("action")
            vault = self.executor.vault
            vault._ensure()
            if action == "save":
                filename = m.get("filename")
                content = str(m.get("content", ""))
                title = m.get("title") or (content.strip().splitlines() or ["Note"])[0].replace("# ", "").strip()[:60]
                if filename:
                    p = vault.notes / Path(filename).name
                else:
                    import re
                    slug = re.sub(r"[^a-z0-9]+", "-", " ".join(title.lower().split()[:6])).strip("-")[:50] or "note"
                    p = vault.notes / f"{time.strftime('%Y-%m-%d_%H%M%S')}_{slug}.md"
                p.write_text(content, encoding="utf-8")
            elif action == "delete":
                filename = m.get("filename")
                if filename:
                    p = vault.notes / Path(filename).name
                    if p.exists():
                        vault.trash.mkdir(parents=True, exist_ok=True)
                        dest = vault.trash / p.name
                        shutil.move(str(p), str(dest))
            await self._send_vault_data()
        elif t == "open_path":
            path_str = str(m.get("path", "")).strip()
            if path_str:
                try:
                    p = Path(path_str).expanduser().resolve()
                    if p.is_dir():
                        res = self.executor.op_open_folder({"path": str(p)})
                    else:
                        res = self.executor.op_open_file({"path": str(p)})
                    msg = res.get("msg", f"Opened {p.name}")
                    await self.broadcast({"type": "say", "text": msg})
                except Exception as e:
                    await self.broadcast({"type": "error", "message": str(e)})
        elif t == "list_folder":
            path_str = str(m.get("path", "")).strip()
            if path_str:
                try:
                    res = self.executor.op_list_folder({"path": path_str})
                    await self.broadcast({
                        "type": "folder_listing",
                        "folder": res.get("folder", Path(path_str).name),
                        "path": res.get("path", path_str),
                        "parent_path": res.get("parent_path"),
                        "items": res.get("items", []),
                        "recursive_items": res.get("recursive_items", []),
                    })
                    await self.broadcast({"type": "say", "text": res.get("msg", f"Listed {Path(path_str).name}")})
                except Exception as e:
                    await self.broadcast({"type": "error", "message": str(e)})
        elif t in ("local_confirm_response", "capture_decision"):
            fut = self._pending.get(m.get("id"))
            if fut and not fut.done():
                fut.set_result(m)

    def _fire(self, coro):
        """Schedule a coroutine on self.loop whether called from the loop thread or a worker thread."""
        if not self.loop or not self.loop.is_running():
            return
        try:
            cur = asyncio.get_running_loop()
        except RuntimeError:
            cur = None
        if cur is self.loop:
            self.loop.create_task(coro)
        else:
            asyncio.run_coroutine_threadsafe(coro, self.loop)

    def _start_mic(self):
        if self._listener and self._listener.active:
            return
        try:
            from client.speech import SpeechListener
            self._listener = SpeechListener(backend=config.STT_ENGINE, lang=config.SPEECH_LANG)
        except Exception as e:
            self._fire(self.broadcast({"type": "error", "message": f"Microphone setup error: {e}"}))
            return

        last_time = 0.0

        def on_level(level: float, speaking: bool):
            nonlocal last_time
            now = time.monotonic()
            if now - last_time > 0.08:
                last_time = now
                self._fire(self.broadcast({"type": "mic", "on": True, "level": level, "speaking": speaking, "engine": "local"}))

        def on_audio(pcm_bytes: bytes):
            self._fire(self._on_local_audio_captured(pcm_bytes))

        def on_error(err: str):
            self._fire(self._on_local_mic_error(err))

        self._listener.start(on_audio, on_error, on_level)
        self._fire(self.broadcast({"type": "mic", "on": True, "level": 0.0, "speaking": False, "engine": "local"}))

    def _stop_mic(self):
        if self._listener:
            self._listener.stop()
        self._fire(self.broadcast({"type": "mic", "on": False, "engine": "local"}))

    def _cancel_mic(self):
        if self._listener:
            self._listener.cancel()
        self._fire(self.broadcast({"type": "mic", "on": False, "engine": "local"}))

    async def _on_local_audio_captured(self, pcm_bytes: bytes):
        await self.broadcast({"type": "mic", "on": False, "engine": "local"})
        if not pcm_bytes:
            await self.broadcast({"type": "heard", "text": ""})
            await self.broadcast({"type": "say", "text": "I didn't hear anything."})
            return
        # Forward complete audio to backend server in one shot
        self.net.send({"type": "audio", "data": base64.b64encode(pcm_bytes).decode("ascii")})
        if hasattr(self.net, "send_bytes"):
            self.net.send_bytes(pcm_bytes)

    async def _on_local_mic_error(self, err: str):
        await self.broadcast({"type": "mic", "on": False, "engine": "local"})
        await self.broadcast({"type": "error", "message": f"Microphone error: {err}"})

    async def _send_vault_data(self, target_sock=None):
        """Broadcasts current tasks and notes to the UI in real-time."""
        try:
            vault = self.executor.vault
            raw_tasks = vault._load()
            tasks = [{"id": i, "done": d, "text": t} for i, (d, t) in enumerate(raw_tasks)]
            notes = []
            for p in vault.files()[:30]:
                try:
                    body = p.read_text(encoding="utf-8", errors="ignore")
                    first_line = (body.strip().splitlines() or [""])[0].replace("# ", "").strip()
                    notes.append({
                        "filename": p.name,
                        "title": first_line or p.stem.split("_", 2)[-1].replace("-", " "),
                        "content": body,
                        "mtime": p.stat().st_mtime,
                    })
                except Exception:
                    pass
            payload = {"type": "vault_data", "tasks": tasks, "notes": notes}
            if target_sock:
                await target_sock.send_json(payload)
            else:
                await self.broadcast(payload)
        except Exception:
            pass

    async def _send_schedule_data(self, target_sock=None, open_tab: bool = False):
        """Broadcasts current local timetable slots to the UI in real-time."""
        try:
            from datetime import datetime
            rows = self.db.slots() if self.db else []
            slots = []
            for r in rows:
                title = str(r[3])
                is_test = "[TEST]" in title or "test" in title.lower() or "exit" in title.lower()
                clean_title = title.replace("[TEST]", "").strip()
                slots.append({
                    "weekday": int(r[0]),
                    "start": str(r[1]),
                    "end": str(r[2]),
                    "title": clean_title,
                    "location": str(r[4] or "Home Lab"),
                    "is_test": is_test,
                })
            prof = self.db.profile() if self.db else {}
            payload = {
                "type": "schedule_data",
                "slots": slots,
                "profile": prof,
                "sub_batch": prof.get("sub_batch", ""),
                "full_batch": prof.get("full_batch", ""),
                "home_lab": prof.get("home_lab", ""),
                "primary_ta": prof.get("primary_ta", ""),
                "cohort": prof.get("cohort", ""),
                "today_weekday": datetime.now().weekday(),
                "time_now": datetime.now().strftime("%H:%M"),
                "openTab": open_tab,
            }
            if target_sock:
                await target_sock.send_json(payload)
            else:
                await self.broadcast(payload)
        except Exception as e:
            print(f"[agent] send_schedule_data failed: {e}", flush=True)

    async def _handle_login(self, user_id: str, password: str, new_password: str = ""):
        """POST /auth/login on the central server, persist JWT, reconnect."""
        import urllib.request
        import urllib.error
        if not user_id or not password:
            await self.broadcast({"type": "error", "message": "Enter user id and password."})
            return
        # Derive HTTP base from WebSocket URL: ws://host:port/ws/... → http://host:port
        ws = config.SERVER_URL
        http = ws.replace("wss://", "https://").replace("ws://", "http://").split("/ws")[0].rstrip("/")
        url = f"{http}/auth/login"
        payload = {"user_id": user_id, "password": password}
        if new_password:
            payload["new_password"] = new_password
        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            try:
                detail = json.loads(detail).get("error") or detail
            except Exception:
                pass
            await self.broadcast({"type": "error", "message": f"{detail}"})
            await self.broadcast({"type": "auth_state", "authenticated": False})
            return
        except Exception as e:
            await self.broadcast({"type": "error", "message": f"Login failed: {e}"})
            await self.broadcast({"type": "auth_state", "authenticated": False})
            return

        if data.get("must_change_password"):
            print(f"[agent] trainee password change required: user_id='{data.get('user_id')}'", flush=True)
            await self.broadcast({
                "type": "must_change_password",
                "user_id": data.get("user_id"),
                "name": data.get("name") or data.get("user_id"),
                "message": data.get("message") or "Password change required. Please set a new password.",
            })
            return

        token = data.get("token") or ""
        if not token:
            await self.broadcast({"type": "error", "message": "Server returned no token."})
            return
        config.save_token(token)
        self.net.token = token
        print(f"[agent] trainee sign-in successful: user_id='{data.get('user_id')}', batch='{data.get('batch')}'", flush=True)
        # Force reconnect so the next auth frame uses the JWT
        try:
            self.net.reconnect()
        except Exception:
            pass
        await self.broadcast({
            "type": "auth_state",
            "authenticated": True,
            "user_id": data.get("user_id"),
            "name": data.get("name"),
            "batch": data.get("batch"),
        })

    def push_shell(self, action: str):
        """Thread-safe: tell the page something happened in the desktop shell (e.g. the global hotkey was pressed)."""
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.broadcast({"type": "shell", "action": action}), self.loop)

    async def model_glb(self, request):
        candidates = [
            STATIC / "model.glb",
            Path("frontend/public/model.glb"),
            Path("model.glb"),
            Path("data/model.glb"),
        ]
        if config.AVATAR_GLB:
            candidates.insert(0, Path(config.AVATAR_GLB))
        for p in candidates:
            if p.is_file():
                return web.FileResponse(p, headers={"Cache-Control": "no-cache"})
        raise web.HTTPNotFound()

    async def avatar(self, request):
        path = Path(config.AVATAR_GLB) if config.AVATAR_GLB else None
        if not path or not path.is_file():
            raise web.HTTPNotFound()
        return web.FileResponse(path, headers={"Cache-Control": "max-age=3600"})

    async def start_server(self, host: str = "127.0.0.1"):
        """Serve the UI. Uses the configured port, or any free one if it is taken. Returns the URL to open."""
        self.runner = web.AppRunner(self.build_app())
        await self.runner.setup()
        for port in (self.port, 0):
            try:
                site = web.TCPSite(self.runner, host, port)
                await site.start()
                self.port = site._server.sockets[0].getsockname()[1]
                return f"http://127.0.0.1:{self.port}/"
            except OSError:
                continue
        raise RuntimeError("could not open a local port")

    def build_app(self) -> web.Application:
        app = web.Application(middlewares=[self._guard])
        app.router.add_get("/", self.index)
        app.router.add_get("/ws", self.ws)
        app.router.add_get("/health", lambda r: web.json_response({"ok": True}))
        app.router.add_get("/avatar.glb", self.avatar)
        app.router.add_get("/model.glb", self.model_glb)
        if (STATIC / "assets").is_dir():
            app.router.add_static("/assets", STATIC / "assets")
        return app

    # ------------------------------------------------------------------ lifecycle
    def start_background(self):
        """Network link, file index, activity sampler, and the thread that moves server messages onto the event loop."""
        threading.Thread(target=self.executor.index.refresh, daemon=True).start()
        if self.sampler:
            self.sampler.start()
        try:
            self.db.prune(config.CHAT_KEEP_DAYS, config.AUDIT_KEEP_DAYS)
        except Exception:
            pass
        self.net.start()

        def pump():
            while True:
                m = self.net.inbox.get()
                asyncio.run_coroutine_threadsafe(self.on_server_msg(m), self.loop)
        threading.Thread(target=pump, daemon=True, name="pump").start()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="trainee-agent", description="Local agent for the Trainee Assistant React UI")
    ap.add_argument("--port", type=int, default=int(__import__("os").getenv("ASSISTANT_AGENT_PORT", "8777")))
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args(argv)

    from client.device.executor import DeviceExecutor
    from client.net import Net
    from client.sensors.activity import ActivitySampler
    net = Net()
    agent = Agent(net, DeviceExecutor(), ActivitySampler(net.send), a.port)

    async def on_start(app):
        agent.loop = asyncio.get_running_loop()
        agent.start_background()
    app = agent.build_app()
    app.on_startup.append(on_start)
    url = f"http://127.0.0.1:{a.port}/"
    print(f"Trainee Assistant agent running. Open {url}   (server: {config.SERVER_URL})")
    if not a.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    web.run_app(app, host="127.0.0.1", port=a.port, print=None)


if __name__ == "__main__":
    main()
