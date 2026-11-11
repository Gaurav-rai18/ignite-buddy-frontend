"""
WebSocket endpoint: auth, framing, size limits and dispatch. No business logic lives here.
One consumer instance = one connected device. Several devices per user and many users per server are expected.
"""
import asyncio
import base64
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from channels.generic.websocket import AsyncWebsocketConsumer

from server import config, llm
from server.domain import orchestrator, policy
from server.domain.session import Cancelled, Session
from server.features.activity.recorder import recorder_for
from shared import protocol as P
from server.data.central import get_central
from server import auth
from . import notifier, presence
from .session_ui import WebSocketUI

log = logging.getLogger("transport")
POOL = ThreadPoolExecutor(max_workers=config.WORKER_THREADS, thread_name_prefix="req")
POLICY_GROUP = "policy"


class AssistantConsumer(AsyncWebsocketConsumer):
    # ---------------- lifecycle ----------------
    async def connect(self):
        """Accept incoming WebSocket connection and initialize session state attributes.

        Initializes batch membership and sync tracking variables up-front to ensure that
        early disconnects or authentication aborts do not reference uninitialized attributes.
        Schedules an authentication timeout to disconnect unauthorized clients.
        """
        self.user = self.session = self.ui = None
        self.busy = False
        self.last_sample = 0.0
        self.device_id = ""
        self.batch = ""
        self.batch_aliases = []
        self.trainee_meta = {}
        self.sync_cursor = 0
        self._transcriber = None
        await self.accept()
        self._auth_timer = asyncio.create_task(self._auth_timeout())

    async def _auth_timeout(self):
        """Disconnect the client if authentication is not completed within the timeout window."""
        await asyncio.sleep(config.AUTH_TIMEOUT)
        if self.user is None:
            await self.close(code=P.CLOSE_UNAUTHORIZED)

    async def disconnect(self, code):
        """Clean up channel groups, active background tasks, and UI locks upon disconnect.

        Safely retrieves batch group subscriptions even if the client disconnects before
        authentication finishes assigning a batch.
        """
        if getattr(self, "_auth_timer", None):
            self._auth_timer.cancel()
        if self.user:
            print(f"[server] [ws] Trainee disconnected: user_id='{self.user.id}' (code={code})", flush=True)
            presence.remove(self.user.id)
            if getattr(self, "_task", None):
                self._task.cancel()
            await self.channel_layer.group_discard(POLICY_GROUP, self.channel_name)
            await self.channel_layer.group_discard(notifier.user_group(self.user.id), self.channel_name)
            for b in getattr(self, "batch_aliases", [getattr(self, "batch", "")]):
                if b and b != "*":
                    try:
                        await self.channel_layer.group_discard(notifier.batch_group(b), self.channel_name)
                    except Exception:
                        pass
            await self.channel_layer.group_discard(notifier.ALL_GROUP, self.channel_name)
            if self.ui:
                self.ui.release_all()

    async def _authenticate(self, msg):
        user = auth.verify_token(msg.get("token", ""))
        if not user:
            await self.close(code=P.CLOSE_UNAUTHORIZED)
            return
        self.user, self.device_id = user, str(msg.get("device_id", ""))[:64]
        try:
            self.sync_cursor = max(0, int(msg.get("sync_cursor", 0)))
        except (TypeError, ValueError):
            self.sync_cursor = 0

        # Resolve trainee's real cohort, batch, sub-batch, and home lab from Django models
        def _resolve_account_info(uid):
            try:
                from server.apps.accounts.models import User as AccountUser
                from server.apps.schedules.models import Schedule
                u = (
                    AccountUser.objects.filter(username__iexact=uid)
                    .select_related("sub_batch__batch__cohort", "sub_batch__lab", "assigned_batch__cohort", "assigned_cohort")
                    .first()
                    or AccountUser.objects.filter(email__iexact=uid)
                    .select_related("sub_batch__batch__cohort", "sub_batch__lab", "assigned_batch__cohort", "assigned_cohort")
                    .first()
                )
                meta = {}
                if u:
                    sb_code = u.sub_batch_code
                    home_lab = (u.sub_batch.lab.name if (u.sub_batch and u.sub_batch.lab) else "")
                    meta = {
                        "user_id": u.username,
                        "name": u.get_full_name() or u.username,
                        "cohort": u.cohort_code,
                        "batch": u.batch_code,
                        "sub_batch": sb_code,
                        "full_batch": u.full_batch_name,
                        "home_lab": home_lab,
                        "primary_ta": "",
                    }
                    act_sched = Schedule.objects.filter(is_active=True).first()
                    if act_sched and act_sched.grid_data:
                        ta_map = act_sched.grid_data.get("ta_mapping", {})
                        if sb_code and sb_code in ta_map:
                            m_entry = ta_map[sb_code]
                            if not meta["home_lab"]:
                                meta["home_lab"] = m_entry.get("home_lab", "")
                            meta["primary_ta"] = m_entry.get("primary_ta", "")
                            meta["backup_ta"] = m_entry.get("backup_ta", "")
                            meta["owner"] = m_entry.get("owner", "")
                return u, meta
            except Exception:
                return None, {}

        acc_user, self.trainee_meta = await asyncio.to_thread(_resolve_account_info, user.id)

        # Collect all batch aliases for this trainee
        batch_candidates = set()
        token_batch = getattr(user, "batch", "")
        if token_batch and token_batch not in ("default", "Unassigned"):
            batch_candidates.add(token_batch)
            if "-" in token_batch:
                for part in token_batch.split("-"):
                    if part.strip():
                        batch_candidates.add(part.strip())

        if acc_user:
            if acc_user.sub_batch_code:
                batch_candidates.add(acc_user.sub_batch_code)
            if acc_user.full_batch_name and acc_user.full_batch_name != "Unassigned":
                batch_candidates.add(acc_user.full_batch_name)
            if acc_user.batch_code:
                batch_candidates.add(acc_user.batch_code)
            if acc_user.cohort_code:
                batch_candidates.add(acc_user.cohort_code)

        primary_batch = (
            (acc_user.sub_batch_code if acc_user else None)
            or (acc_user.full_batch_name if acc_user and acc_user.full_batch_name != "Unassigned" else None)
            or (token_batch if token_batch and token_batch != "default" else None)
            or "default"
        )
        batch_candidates.add(primary_batch)
        self.batch = primary_batch
        self.batch_aliases = [b for b in batch_candidates if b and b not in ("default", "Unassigned")]
        if not self.batch_aliases:
            self.batch_aliases = [primary_batch]

        # Update central.db trainee profile and batch
        display_name = (acc_user.get_full_name() if acc_user else None) or user.name or user.id
        await asyncio.to_thread(get_central().create_trainee, user.id, display_name, self.batch)
        await asyncio.to_thread(get_central().set_batch, user.id, self.batch)

        self.ui = WebSocketUI(self, asyncio.get_running_loop())
        self.session = Session.create(user, self.ui)
        presence.add(user.id)
        await self.channel_layer.group_add(POLICY_GROUP, self.channel_name)
        await self.channel_layer.group_add(notifier.user_group(user.id), self.channel_name)
        for b in self.batch_aliases:
            if b and b != "*":
                await self.channel_layer.group_add(notifier.batch_group(b), self.channel_name)
        await self.channel_layer.group_add(notifier.ALL_GROUP, self.channel_name)
        rec = recorder_for(self.session.store)
        await asyncio.to_thread(rec.purge_old)
        print(f"[server] [ws] Trainee authenticated on WebSocket: user_id='{user.id}', name='{user.name}', batch='{self.batch}', aliases={self.batch_aliases}, device='{self.device_id}'", flush=True)
        await self.send_json({"type": "hello_ok", "user": {"id": user.id, "name": user.name}, "debug": config.DEBUG,
                              "models": {"chat": config.CHAT_MODEL, "fast": config.FAST_MODEL},
                              "tracking": rec.pause_state(), "protocol": P.PROTOCOL_VERSION,
                              "capabilities": policy.capabilities(user.id),
                              "trainee_meta": self.trainee_meta})
        await self.send_json({"type": "policy", **policy.snapshot(user.id)})
        await self._push_sync()                              # whatever the admin published since this PC last synced

    async def _push_sync(self):
        aliases = list(getattr(self, "batch_aliases", [self.batch]))
        delta = await asyncio.to_thread(get_central().changes_since, aliases, self.sync_cursor)
        if delta["assignments"] or delta["timetable"]:
            self.sync_cursor = delta["cursor"]
            await self.send_json({
                "type": "sync",
                "cursor": delta["cursor"],
                "assignments": delta["assignments"],
                "timetable": delta["timetable"],
                "trainee_meta": getattr(self, "trainee_meta", {}),
            })

    # ---------------- group events ----------------
    async def sync_push(self, event):
        if self.user and not policy.is_blocked(self.user.id):
            await self._push_sync()

    async def policy_update(self, event):
        if not self.user:
            return
        snap = policy.snapshot(self.user.id)
        await self.send_json({"type": "policy", **snap})
        if snap["blocked"]:
            self.ui.release_all()

    async def push_message(self, event):
        if self.user and not policy.is_blocked(self.user.id):
            await self.send_json(event["msg"])

    async def trainee_notification(self, event):
        if self.user:
            await self.send_json({
                "type": "notification",
                "kind": event.get("kind", "broadcast"),
                "notification_id": event.get("notification_id"),
                "title": event.get("title", ""),
                "message": event.get("message", ""),
                "text": event.get("text", ""),
                "created_at": event.get("created_at", ""),
            })

    # ---------------- framing ----------------
    async def send_json(self, msg):
        await self.send(text_data=json.dumps(msg))

    @property
    def transcriber(self):
        if self._transcriber is None:
            from server.stt.transcriber import build_from_config
            self._transcriber = build_from_config(config)
        return self._transcriber

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data is not None:
            if self.user is not None:
                await self.on_audio({"data": bytes_data})
            return
        try:
            msg = json.loads(text_data or "")
            kind = msg["type"]
        except (ValueError, KeyError, TypeError):
            return
        if self.user is None:
            if kind == "auth":
                await self._authenticate(msg)
            return
        handler = getattr(self, f"on_{kind}", None) if isinstance(kind, str) and kind.isidentifier() else None
        if handler:
            await handler(msg)

    async def on_audio(self, msg):
        """Processes a full audio recording sent in one shot from the client."""
        if await self._blocked():
            return
        raw = msg.get("data")
        if isinstance(raw, str):
            try:
                audio_bytes = base64.b64decode(raw)
            except Exception:
                await self.send_json({"type": "error", "message": "Malformed audio payload"})
                return
        elif isinstance(raw, (bytes, bytearray)):
            audio_bytes = bytes(raw)
        else:
            await self.send_json({"type": "error", "message": "No audio data received"})
            return

        if len(audio_bytes) > P.MAX_AUDIO_BYTES:
            await self.send_json({"type": "error", "message": "Audio recording is too long"})
            return

        await self.send_json({"type": "state", "state": "thinking"})

        from server.stt.transcriber import SttError, SttUnavailable

        try:
            text = await asyncio.get_running_loop().run_in_executor(
                POOL, self.transcriber.transcribe, audio_bytes
            )
        except SttUnavailable as e:
            log.warning("STT unavailable: %s", e)
            await self.send_json({"type": "transcript", "text": "", "final": True})
            await self.send_json({"type": "error", "message": str(e)})
            await self.send_json({"type": "state", "state": "idle"})
            return
        except SttError as e:
            log.error("STT error: %s", e)
            await self.send_json({"type": "transcript", "text": "", "final": True})
            await self.send_json({"type": "error", "message": str(e)})
            await self.send_json({"type": "state", "state": "idle"})
            return
        except Exception as e:
            log.exception("Unexpected STT failure")
            await self.send_json({"type": "transcript", "text": "", "final": True})
            await self.send_json({"type": "error", "message": f"Speech recognition failed: {e}"})
            await self.send_json({"type": "state", "state": "idle"})
            return

        if not text:
            await self.send_json({"type": "transcript", "text": "", "final": True})
            await self.send_json({"type": "say", "text": "I didn't catch that."})
            await self.send_json({"type": "state", "state": "idle"})
            return

        # Broadcast the recognized transcript to the client so the UI shows the question/command
        await self.send_json({"type": "transcript", "text": text, "final": True})
        # Execute query through the deterministic skills / HNSW RAG / default browser pipeline
        self._spawn(text)

    # ---------------- simple messages ----------------
    async def on_ping(self, msg): await self.send_json({"type": "pong"})
    async def on_settings(self, msg): pass
    async def on_playback_done(self, msg): pass

    async def on_sync_request(self, msg):
        """Allows client to request timetable sync or full refresh."""
        if msg.get("force"):
            self.sync_cursor = 0
        else:
            try:
                self.sync_cursor = max(0, int(msg.get("sync_cursor", self.sync_cursor)))
            except (TypeError, ValueError):
                pass
        await self._push_sync()

    async def on_cancel(self, msg):
        self.ui.release_all()

    async def on_dev_set_blocked(self, msg):
        if not config.DEBUG:
            return
        policy.set_blocked(bool(msg.get("blocked")))
        await self.channel_layer.group_send(POLICY_GROUP, {"type": "policy.update"})

    # replies to server-initiated questions
    async def on_confirm_response(self, msg): self.ui.resolve(msg.get("id"), bool(msg.get("approved")))
    async def on_choose_response(self, msg): self.ui.resolve(msg.get("id"), msg.get("choice") or None)
    async def on_device_result(self, msg): self.ui.resolve(msg.get("id"), msg)

    async def on_capture_response(self, msg):
        img = msg.get("image_b64")
        if not img or len(img) * 3 // 4 > P.MAX_SCREENSHOT_BYTES:
            self.ui.resolve(msg.get("id"), None)
            return
        self.ui.resolve(msg.get("id"), {"image_b64": img, "app": str(msg.get("app", ""))[:P.MAX_APP_LEN],
                                        "title": str(msg.get("title", ""))[:P.MAX_TITLE_LEN],
                                        "include_file": bool(msg.get("include_file"))})

    # ---------------- activity samples from the client ----------------
    async def on_activity_sample(self, msg):
        now = time.time()
        if now - self.last_sample < config.SAMPLE_MIN_INTERVAL:          # flood guard
            return
        self.last_sample = now
        rec = recorder_for(self.session.store)
        await asyncio.to_thread(rec.ingest, msg.get("app"), msg.get("title"), bool(msg.get("idle")), now, id(self))

    # ---------------- requests ----------------
    async def _blocked(self) -> bool:
        if policy.is_blocked(self.user.id):
            await self.send_json({"type": "blocked", "reason": policy.snapshot(self.user.id)["reason"]})
            return True
        return False

    async def on_text(self, msg):
        text = str(msg.get("text", "")).strip()[:P.MAX_TEXT]
        if text and not await self._blocked():
            self._spawn(text)

    def _spawn(self, text):
        """Run the request in the background so this consumer keeps reading messages (device_result, cancel...).
        Channels handles messages one at a time per connection: awaiting the request here would deadlock."""
        self._task = asyncio.create_task(self._run(text))

    async def _run(self, text):
        if self.busy:
            await self.send_json({"type": "error", "message": "Still working on the previous request."})
            return
        self.busy = True
        self.ui.cancel.clear()
        try:
            spoken = await asyncio.get_running_loop().run_in_executor(POOL, self._work, text)
            if spoken:
                await self.send_json({"type": "speak", "text": spoken})
        finally:
            self.busy = False
            await self.send_json({"type": "state", "state": "idle"})

    def _work(self, text):
        try:
            return orchestrator.process(self.session, text)
        except Cancelled:
            return None
        except llm.LLMError as e:
            self.ui.say(str(e))
        except Exception:
            log.exception("request failed")
            self.ui.say("Something went wrong on the server.")
