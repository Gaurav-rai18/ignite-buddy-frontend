"""Adapter that lets worker-thread services talk to ONE websocket client (blocking request/response helpers)."""
import asyncio
import itertools
import threading

from server import config
from shared import protocol as P
from server.domain.session import Cancelled


class WebSocketUI:
    def __init__(self, consumer, loop):
        self.c, self.loop = consumer, loop
        self.cancel = threading.Event()
        self._pending: dict[str, "asyncio.Future"] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    # ---- fire and forget ----
    def _emit(self, msg):
        try:
            asyncio.run_coroutine_threadsafe(self.c.send_json(msg), self.loop).result(timeout=10)
        except Exception:
            self.cancel.set()

    def state(self, s): self._emit({"type": "state", "state": s})
    def say(self, text): self._emit({"type": "say", "text": text})
    def token(self, text): self._emit({"type": "token", "text": text})
    def end_message(self): self._emit({"type": "message_end"})
    def push(self, msg): self._emit(msg)

    # ---- blocking round trips ----
    def _ask(self, msg, timeout=None):
        import concurrent.futures
        if self.cancel.is_set():
            raise Cancelled
        rid = f"r{next(self._ids)}"
        fut: concurrent.futures.Future = concurrent.futures.Future()
        with self._lock:
            self._pending[rid] = fut
        self._emit({**msg, "id": rid})
        try:
            return fut.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return None
        finally:
            with self._lock:
                self._pending.pop(rid, None)

    def resolve(self, rid, value) -> bool:
        """Called by the consumer when the client answers."""
        with self._lock:
            fut = self._pending.get(rid)
        if fut and not fut.done():
            fut.set_result(value)
            return True
        return False

    def release_all(self):
        """Cancel / disconnect: unblock every waiting worker thread."""
        self.cancel.set()
        with self._lock:
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_result(None)

    def confirm(self, title, preview="") -> bool:
        return bool(self._ask({"type": "confirm_request", "title": title, "preview": preview}))

    def choose(self, question, options):
        return self._ask({"type": "choose_request", "question": question, "options": options})

    def capture_screen(self):
        return self._ask({"type": "capture_request"})

    def device_call(self, op, args) -> P.DeviceResult:
        if op not in P.DEVICE_OPS:
            return P.DeviceResult.error(f"Unknown device operation {op}")
        res = self._ask({"type": "device_call", "op": op, "args": args}, timeout=config.DEVICE_TIMEOUT)
        if res is None:
            if self.cancel.is_set():
                raise Cancelled
            return P.DeviceResult.error("Your computer did not answer in time.")
        return P.DeviceResult.from_wire(res)
