"""WebSocket link to the central server: auto-reconnect, first-message auth, thread-safe inbox for the UI loop."""
import json
import queue
import threading
import time

from client import config
from shared import protocol as P


class Net:
    def __init__(self, url=None, token=None, device_id=None):
        self.url, self.token, self.device_id = url or config.SERVER_URL, token or config.TOKEN or config.load_saved_token(), device_id or config.DEVICE_ID
        self.inbox: queue.Queue = queue.Queue()
        self.ws = None
        self._stop = False
        self.connected = False
        self.auth_extra = None
        self._reconnect_event = threading.Event()
        self._auth_failed = not bool(self.token)

    def start(self):
        threading.Thread(target=self._loop, daemon=True, name="net").start()

    def stop(self):
        self._stop = True
        self._reconnect_event.set()
        if self.ws:
            self.ws.close()

    def reconnect(self):
        """Drop the current socket so the background loop opens a new one with the current token."""
        self._auth_failed = False
        self._reconnect_event.set()
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass
        self.ws = None

    def _loop(self):
        import websocket                                   # pip install websocket-client
        delay = 1
        while not self._stop:
            if not self.token:
                self._auth_failed = True
                self._reconnect_event.wait(timeout=120)
                continue

            self._reconnect_event.clear()
            self.ws = websocket.WebSocketApp(
                self.url, on_open=self._on_open, on_message=self._on_message, on_close=self._on_close,
                on_error=self._on_error)
            try:
                self.ws.run_forever(**self._proxy_kwargs())
            except Exception as e:                           # proxy / TLS / DNS problems must be visible, not silent
                self._on_error(self.ws, e)
            if self._stop:
                return

            if self._auth_failed:
                # Wait until login provides a new token and calls reconnect(), or retry after 120s
                self._reconnect_event.wait(timeout=120)
                self._auth_failed = False
                continue

            time.sleep(delay)
            delay = min(delay * 2, 15)

    def _proxy_kwargs(self) -> dict:
        from urllib.parse import urlparse
        host = urlparse(self.url).hostname or "127.0.0.1"
        is_local = host in ("127.0.0.1", "localhost", "::1", "0.0.0.0")
        if is_local or config.PROXY.lower() in ("none", "direct", "off"):
            return {"http_no_proxy": [host, "127.0.0.1", "localhost"]}
        if config.PROXY.lower() not in ("env", "system"):
            p = urlparse(config.PROXY if "://" in config.PROXY else "http://" + config.PROXY)
            return {
                "http_proxy_host": p.hostname,
                "http_proxy_port": p.port or 8080,
                "http_proxy_auth": (p.username, p.password) if p.username else None,
                "http_no_proxy": [host, "127.0.0.1", "localhost"],
            }
        return {"http_no_proxy": [host, "127.0.0.1", "localhost"]}

    def _on_open(self, ws):
        # the token travels in the first message, never in the URL (URLs end up in proxy logs)
        extra = {}
        try:
            extra = self.auth_extra() if self.auth_extra else {}          # e.g. the local sync cursor
        except Exception:
            pass
        ws.send(json.dumps({"type": "auth", "token": self.token, "device_id": self.device_id,
                            "version": P.PROTOCOL_VERSION, **extra}))
        self.connected = True
        self.inbox.put({"type": "_connected"})

    def _on_error(self, ws, error):
        self.inbox.put({"type": "_error", "error": f"{type(error).__name__}: {error}"[:300]})

    def _on_close(self, ws, code, reason):
        self.connected = False
        if code == P.CLOSE_UNAUTHORIZED:
            self._auth_failed = True
        self.inbox.put({"type": "_disconnected", "code": code})

    def _on_message(self, ws, data):
        try:
            self.inbox.put(json.loads(data))
        except ValueError:
            pass

    def send(self, msg: dict):
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps(msg))
            except Exception:
                pass

    def send_bytes(self, data: bytes):
        if self.ws and self.connected:
            try:
                self.ws.send(data, opcode=0x2)
            except Exception:
                pass
