"""Server runtime settings.

Load order (later wins only for variables not already set in the process env):
  1. Process environment
  2. ``.env`` in the current working directory
  3. ``ASSISTANT_ENV_FILE`` if set
  4. Built-in defaults below

Nothing here is per-user. Credentials for models stay on the server only.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # optional until pip install python-dotenv
    def load_dotenv(*_a, **_k):
        return False


def _load_env_files() -> None:
    # Do not override variables already exported in the shell / process manager.
    explicit = os.getenv("ASSISTANT_ENV_FILE")
    if explicit:
        load_dotenv(explicit, override=False)
    load_dotenv(Path.cwd() / ".env", override=False)
    # Optional server-specific file
    load_dotenv(Path.cwd() / ".env.server", override=False)


_load_env_files()


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    return float(raw) if raw not in (None, "") else default


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    return int(raw) if raw not in (None, "") else default


def _csv(key: str, default: str) -> list[str]:
    return [p.strip() for p in _env(key, default).split(",") if p.strip()]


# ---- LLM gateway (organisation Ollama / compatible) ----
_base = _env("OLLAMA_BASE_URL") or _env("OLLAMA_HOST") or "http://localhost:11434"
LLM_BASE_URL = (_base if "://" in _base else "http://" + _base).rstrip("/")
LLM_API_KEY = _env("OLLAMA_API_KEY")
LLM_AUTH_HEADER = _env("OLLAMA_AUTH_HEADER", "Authorization")
LLM_TIMEOUT = _env_float("OLLAMA_TIMEOUT", 600.0)
LLM_CONNECT_TIMEOUT = _env_float("OLLAMA_CONNECT_TIMEOUT", 10.0)
LLM_PROXY = _env("OLLAMA_PROXY", "none")  # none | env | URL
LLM_USE_SYSTEM_CERTS = _env_bool("OLLAMA_USE_SYSTEM_CERTS", False)
LLM_CA_BUNDLE = _env("OLLAMA_CA_BUNDLE")
LLM_VERIFY_SSL = _env("OLLAMA_VERIFY_SSL", "1") != "0"
FAST_MODEL = _env("FAST_MODEL", "qwen2.5:3b")
CHAT_MODEL = _env("CHAT_MODEL", "gpt-oss:20b")
EMBED_MODEL = _env("EMBED_MODEL", "nomic-embed-text")
NUM_CTX_PLANNER = _env_int("NUM_CTX_PLANNER", 4096)
NUM_CTX_CHAT = _env_int("NUM_CTX_CHAT", 131072)  # 128K context window
RAG_MEMORY_TURNS = _env_int("RAG_MEMORY_TURNS", 15)  # Recent turns to load from SQLite memory

# ---- process / network ----
HOST = _env("ASSISTANT_HOST", "127.0.0.1")
PORT = _env_int("ASSISTANT_PORT", 8765)
DEBUG = _env_bool("ASSISTANT_DEBUG", False)
ALLOWED_HOSTS = _csv("ASSISTANT_ALLOWED_HOSTS", "127.0.0.1,localhost")
REDIS_URL = _env("REDIS_URL")
RUN_BACKGROUND = not _env_bool("ASSISTANT_DISABLE_BACKGROUND", False)
WORKER_THREADS = _env_int("ASSISTANT_WORKER_THREADS", 64)
DEVICE_TIMEOUT = _env_float("ASSISTANT_DEVICE_TIMEOUT", 900.0)
AUTH_TIMEOUT = _env_float("ASSISTANT_AUTH_TIMEOUT", 5.0)
SAMPLE_MIN_INTERVAL = _env_float("ACTIVITY_MIN_INTERVAL", 2.0)
TIMEZONE = _env("ASSISTANT_TIMEZONE")  # IANA name; empty = OS zone

# ---- STT (server-side speech-to-text) ----
STT_ENGINE = _env("STT_ENGINE", "google").lower()
STT_OPTIONS = _env("STT_OPTIONS", "{}")
SPEECH_LANG = _env("SPEECH_LANG", "en-US")
STT_PROXY = _env("STT_PROXY", _env("HTTPS_PROXY", _env("https_proxy", "")))
VOSK_MODEL_PATH = _env("VOSK_MODEL_PATH", "")

# ---- authentication ----
TOKENS_ENV = _env("ASSISTANT_TOKENS")  # "tokA:alice,tokB:bob"
SINGLE_TOKEN = _env("ASSISTANT_TOKEN", "dev-token" if DEBUG else "")
ADMIN_TOKEN = _env("ASSISTANT_ADMIN_TOKEN")
# JWT for desktop login; random secret in DEBUG if unset
_jwt = _env("ASSISTANT_JWT_SECRET")
JWT_SECRET = _jwt or (secrets.token_hex(32) if DEBUG else "")
JWT_TTL_HOURS = _env_int("ASSISTANT_JWT_TTL_HOURS", 168)

# ---- databases / data dirs ----
DATABASE_URL = _env("DATABASE_URL")  # empty → SQLite under DATA_DIR
DATA_DIR = Path(_env("ASSISTANT_DATA", str(Path.home() / ".trainee_assistant_server"))).expanduser()
USERS_DIR = DATA_DIR / "users"
ACTIVITY_INTERVAL = _env_float("ACTIVITY_INTERVAL", 5.0)
RETENTION_DAYS = _env_int("RETENTION_DAYS", 14)
PAUSE_TRACKING_WHEN_BLOCKED = _env_bool("PAUSE_TRACKING_WHEN_BLOCKED", True)


def _hhmm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    return int(h), int(m)


DAILY_SUMMARY_AT = _hhmm(_env("DAILY_SUMMARY_AT", "18:00"))
CHAT_HISTORY_TURNS = _env_int("CHAT_HISTORY_TURNS", 10)

# ---- policy / capabilities ----
CAPABILITIES = _env("ASSISTANT_CAPABILITIES")
POLICY_FILE = _env("ASSISTANT_POLICY_FILE")
QUICK_SITES = _env("ASSISTANT_QUICK_SITES")  # JSON object as string

# ---- RAG / knowledge base ----
RAG_RETRIEVERS = _csv("RAG_RETRIEVERS", "kb")
RAG_TOP_K = _env_int("RAG_TOP_K", 5)
RAG_STRICT = _env_bool("RAG_STRICT", True)
KB_PATH = Path(_env("KB_PATH", str(DATA_DIR / "kb"))).expanduser()
KB_MIN_SCORE = _env_float("KB_MIN_SCORE", 0.55)
KB_MAX_FILE_MB = _env_int("KB_MAX_FILE_MB", 50)
KB_IGNITE_HINTS = [
    h.strip().lower()
    for h in _env(
        "KB_IGNITE_HINTS",
        "ignite,smart hiring,trainee,onboarding,induction,ilp,training schedule,assessment,batch,mentor,bootcamp",
    ).split(",")
    if h.strip()
]

# ---- screen help ----
VISION_MODEL = _env("VISION_MODEL")
SCREEN_OCR = _env_bool("SCREEN_OCR", True)
SCREEN_SEND_IMAGE = _env("SCREEN_SEND_IMAGE", "auto")  # auto | never | always
MAX_SCREENSHOT_BYTES = _env_int("MAX_SCREENSHOT_BYTES", 8_000_000)
