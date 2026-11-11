"""
MOCK API-KEY GATEWAY for local testing (stdlib only). Pretend your Mac-hosted models sit behind a key.

  real Ollama (no auth, 127.0.0.1:11434)  <--  this gateway (127.0.0.1:11435, needs a key)  <--  the app

Run:    python mock_gateway.py
Use:    OLLAMA_BASE_URL=http://127.0.0.1:11435   OLLAMA_API_KEY=mock-key-123
Block:  curl -X POST http://127.0.0.1:11435/_admin/block -H "X-Admin-Key: mock-admin-123" -d '{"blocked": true}'
Like the production gateway it logs METADATA ONLY (path, model, status, latency), never prompts or answers.
"""
import hmac
import http.client
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

API_KEY = os.getenv("MOCK_API_KEY", "mock-key-123")
ADMIN_KEY = os.getenv("MOCK_ADMIN_KEY", "mock-admin-123")
UPSTREAM = urlparse(os.getenv("UPSTREAM", "http://127.0.0.1:11434"))
LISTEN_PORT = int(os.getenv("MOCK_GATEWAY_PORT", "11435"))
MODEL_PATHS = ("/api/chat", "/api/generate", "/api/embed", "/api/embeddings")
MAX_BODY = 2_000_000
STATE = {"blocked": False}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"          # body ends when the connection closes -> trivial streaming

    def log_message(self, *args):
        pass

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _key_ok(self) -> bool:
        auth = self.headers.get("Authorization", "")
        return (hmac.compare_digest(auth, f"Bearer {API_KEY}")
                or hmac.compare_digest(self.headers.get("X-API-Key", ""), API_KEY))

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    do_DELETE = do_GET

    def _handle(self):
        t0 = time.time()
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if 0 < length <= MAX_BODY else b""
        status, model = 0, ""
        try:
            if path == "/health":
                status = 200
                return self._json(200, {"status": "ok", "blocked": STATE["blocked"]})
            if path == "/_admin/block":
                if not hmac.compare_digest(self.headers.get("X-Admin-Key", ""), ADMIN_KEY):
                    status = 401
                    return self._json(401, {"error": "bad admin key"})
                STATE["blocked"] = bool(json.loads(body or b"{}").get("blocked"))
                status = 200
                return self._json(200, {"blocked": STATE["blocked"]})
            if not self._key_ok():
                status = 401
                return self._json(401, {"error": "invalid or missing API key"})
            if length > MAX_BODY:
                status = 413
                return self._json(413, {"error": "request too large"})
            if STATE["blocked"] and path in MODEL_PATHS:
                status = 403
                return self._json(403, {"error": "The assistant is disabled during the assessment."})
            if path in MODEL_PATHS:
                try:
                    model = json.loads(body).get("model", "")
                except ValueError:
                    pass
            conn = http.client.HTTPConnection(UPSTREAM.hostname, UPSTREAM.port or 80, timeout=600)
            conn.request(self.command, self.path, body or None,
                         {"Content-Type": self.headers.get("Content-Type", "application/json")})
            resp = conn.getresponse()
            status = resp.status
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.getheader("Content-Type", "application/json"))
            self.end_headers()
            for line in iter(resp.readline, b""):          # stream NDJSON line by line
                self.wfile.write(line)
                self.wfile.flush()
            conn.close()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            if not status:
                status = 502
                try:
                    self._json(502, {"error": f"upstream error: {e}"})
                except Exception:
                    pass
        finally:
            print(f"{time.strftime('%H:%M:%S')} {self.command} {path} model={model or '-'} "
                  f"-> {status} {int((time.time() - t0) * 1000)}ms", flush=True)


if __name__ == "__main__":
    print(f"Mock gateway on http://127.0.0.1:{LISTEN_PORT} -> {UPSTREAM.geturl()}")
    print(f"API key: {API_KEY}   admin key: {ADMIN_KEY}")
    srv = ThreadingHTTPServer(("127.0.0.1", LISTEN_PORT), Handler)
    srv.daemon_threads = True
    srv.serve_forever()
