"""Tests the ChatOllama layer against a FAKE Ollama server mounted under a path prefix (no real Ollama needed)."""
import json, os, threading, tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer

os.environ["ASSISTANT_DATA"] = tempfile.mkdtemp()
SEEN = []


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, obj, ctype="application/json"):
        d = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(200); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        SEEN.append((self.path, dict(self.headers), body))
        if not self.path.startswith("/ollama/"):
            self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers(); return
        if self.path.endswith("/api/embed"):
            return self._send({"model": "m", "embeddings": [[0.1, 0.2] for _ in body["input"]]})
        if self.path.endswith("/api/show"):
            return self._send({"capabilities": ["completion", "vision"], "model_info": {}})
        text = '{"intent": "chat"}' if body.get("format") == "json" else "Hello"
        parts = [text[:3], text[3:]]
        lines = [json.dumps({"model": "m", "message": {"role": "assistant", "content": p}, "done": False}) for p in parts]
        lines.append(json.dumps({"model": "m", "message": {"role": "assistant", "content": ""}, "done": True, "done_reason": "stop"}))
        self._send(("\n".join(lines) + "\n").encode(), "application/x-ndjson")


srv = HTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["OLLAMA_BASE_URL"] = f"127.0.0.1:{srv.server_port}/ollama"       # no scheme on purpose
os.environ["OLLAMA_API_KEY"] = "k123"
os.environ["OLLAMA_PROXY"] = "none"

from server import config, llm
from server.llm import network

assert config.LLM_BASE_URL == f"http://127.0.0.1:{srv.server_port}/ollama", config.LLM_BASE_URL

# text, streaming, json (path prefix + auth header + options)
assert llm.chat_text([{"role": "user", "content": "hi"}]) == "Hello"
assert "".join(llm.chat_stream([{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}])) == "Hello"
assert llm.chat_json("sys", "usr") == {"intent": "chat"}
path, hdr, body = SEEN[-1]
assert path == "/ollama/api/chat" and body["format"] == "json" and body["options"]["temperature"] == 0
assert body["options"]["num_ctx"] == config.NUM_CTX_PLANNER and body["model"] == config.FAST_MODEL
assert {k.lower(): v for k, v in hdr.items()}["authorization"] == "Bearer k123"
chat_body = [b for p, h, b in SEEN if p.endswith("/api/chat") and "format" not in b][0]
assert chat_body["options"]["num_ctx"] == config.NUM_CTX_CHAT and chat_body["think"] is False

# images (screen help) reach the server as base64
list(llm.chat_stream([{"role": "system", "content": "s"}, {"role": "user", "content": "look", "images": ["QUJD"]}]))
assert SEEN[-1][2]["messages"][-1]["images"] == ["QUJD"], SEEN[-1][2]["messages"]

# embeddings + vision capability
assert llm.embed(["a", "b", "c"], "search_query: ") == [[0.1, 0.2]] * 3
assert SEEN[-1][2]["input"] == ["search_query: a", "search_query: b", "search_query: c"]
assert llm.supports_vision("any") is True

# network settings
assert network.httpx_kwargs()["trust_env"] is False
config.LLM_PROXY = "http://proxy.corp:8080"
assert network.httpx_kwargs()["proxy"] == "http://proxy.corp:8080"
config.LLM_PROXY = ""
assert "proxy" not in network.httpx_kwargs() and "trust_env" not in network.httpx_kwargs()
config.LLM_BASE_URL = "https://x.corp:8443/ollama"
assert "verify" not in network.httpx_kwargs()                  # default trust
config.LLM_USE_SYSTEM_CERTS = True
import ssl
assert isinstance(network.httpx_kwargs()["verify"], ssl.SSLContext)
config.LLM_USE_SYSTEM_CERTS, config.LLM_CA_BUNDLE = False, "/nonexistent.pem"
try:
    network.httpx_kwargs(); raise SystemExit("bad CA bundle path should fail")
except FileNotFoundError:
    pass
config.LLM_CA_BUNDLE = ""

# friendly errors
import httpx
from server.llm.errors import explain, LLMError
e = explain(httpx.ConnectError("[SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate in certificate chain"))
assert isinstance(e, LLMError) and "Zscaler" in str(e)
assert "OLLAMA_BASE_URL" in str(explain(httpx.ConnectError("refused")))
assert isinstance(explain(ValueError("x")), ValueError)
print("all llm tests passed")
