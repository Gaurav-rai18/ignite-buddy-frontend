"""Client runtime settings (trainee PC).

Load order (does not override variables already set in the process env):
  1. Process environment
  2. ``.env`` in the current working directory
  3. ``ASSISTANT_ENV_FILE`` if set
  4. ``.env.client`` in the current working directory
  5. Defaults below

The client holds no model credentials.
"""
from __future__ import annotations

import os
import socket
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_a, **_k):
        return False


def _load_env_files() -> None:
    explicit = os.getenv("ASSISTANT_ENV_FILE")
    if explicit:
        load_dotenv(explicit, override=False)
    load_dotenv(Path.cwd() / ".env", override=False)
    load_dotenv(Path.cwd() / ".env.client", override=False)


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


def _roots(env: str, default_names: list[str]) -> list[Path]:
    """Folder allowlists: env is os.pathsep-separated absolute/relative paths, else ~/<name> for each default."""
    raw = _env(env)
    if raw:
        return [Path(p).expanduser().resolve() for p in raw.split(os.pathsep) if p.strip()]
    return [(Path.home() / d).resolve() for d in default_names]


# ---- link to central server ----
SERVER_URL = _env("ASSISTANT_URL", "ws://127.0.0.1:8765/ws/assistant/")
TOKEN = _env("ASSISTANT_TOKEN")  # empty → try saved JWT from desktop login
DEVICE_ID = _env("ASSISTANT_DEVICE_ID", socket.gethostname())
# none = direct; env = honour HTTP(S)_PROXY; or a proxy URL
PROXY = _env("ASSISTANT_PROXY", "none")

# ---- path allowlists (device executor enforces these) ----
SEARCH_ROOTS = _roots("ASSISTANT_SEARCH_ROOTS", ["Documents", "Desktop", "Downloads"])
SCRIPT_ROOTS = _roots("ASSISTANT_SCRIPT_ROOTS", ["Documents", "Desktop"])
WRITE_ROOTS = _roots("ASSISTANT_WRITE_ROOTS", ["Documents", "Desktop"])
DEFAULT_PARENT = WRITE_ROOTS[0] if WRITE_ROOTS else Path.home().resolve()
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "AppData", "$RECYCLE.BIN"}
MAX_DEPTH = _env_int("ASSISTANT_MAX_DEPTH", 5)
SCRIPT_TIMEOUT = _env_int("ASSISTANT_SCRIPT_TIMEOUT", 300)
INDEX_REFRESH_SECONDS = _env_int("ASSISTANT_INDEX_REFRESH_SECONDS", 1800)

# dedicated assistant folder on THIS computer: Notes/*.md and Tasks.md
HOME_DIR = Path(_env("ASSISTANT_HOME", str(Path.home() / "Documents" / "TraineeAssistant"))).expanduser()
HOME = HOME_DIR  # alias used by some call sites

# documents (for /index)
DOC_EXTS = {".pdf", ".txt", ".md", ".py", ".js", ".java"}
MAX_DOC_BYTES = _env_int("ASSISTANT_MAX_DOC_BYTES", 5_000_000)
MAX_DOCS_PER_FOLDER = _env_int("ASSISTANT_MAX_DOCS_PER_FOLDER", 2000)
MAX_FILE_BYTES = _env_int("ASSISTANT_MAX_FILE_BYTES", 200_000)

# activity sampling
ACTIVITY_INTERVAL = _env_float("ACTIVITY_INTERVAL", 5.0)
IDLE_AFTER = _env_float("ACTIVITY_IDLE_AFTER", 120.0)
APP_BLOCKLIST = [x.strip().lower() for x in _env("ACTIVITY_BLOCKLIST", "").split(",") if x.strip()]

# ---- local agent ----
AGENT_PORT = _env_int("ASSISTANT_AGENT_PORT", 8777)
HOTKEY = _env("ASSISTANT_HOTKEY", "ctrl+alt+space")
AVATAR_GLB = _env("ASSISTANT_AVATAR_GLB")
SCREEN_MAX_DIM = _env_int("SCREEN_MAX_DIM", 1280)
MIC_RATE = 16000

# ---- STT settings (audio is transcribed on backend server) ----
STT_ENGINE = _env("STT_ENGINE", "google").lower()
STT_OPTIONS = _env("STT_OPTIONS", "{}")
SPEECH_LANG = _env("ASSISTANT_SPEECH_LANG", "en-US")
STT_INTERIM_SECONDS = _env_float("STT_INTERIM_SECONDS", 1.5)
STT_MAX_SECONDS = _env_int("STT_MAX_SECONDS", 30)

# ---- local SQLite ----
CLIENT_DATA = Path(_env("ASSISTANT_CLIENT_DATA", str(Path.home() / ".trainee_assistant"))).expanduser()
LOCAL_DB = Path(_env("ASSISTANT_LOCAL_DB", str(CLIENT_DATA / "local.db"))).expanduser()
TOKEN_FILE = Path(_env("ASSISTANT_TOKEN_FILE", str(CLIENT_DATA / "auth_token"))).expanduser()
CHAT_KEEP_DAYS = _env_int("CHAT_KEEP_DAYS", 90)
AUDIT_KEEP_DAYS = _env_int("AUDIT_KEEP_DAYS", 30)

# ---- shell selection (see desktop/launcher.py) ----
SHELL = _env("ASSISTANT_SHELL", "auto")  # auto | electron | pyside6
ELECTRON_DIR = _env("ASSISTANT_ELECTRON_DIR")


def load_saved_token() -> str:
    try:
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def save_token(token: str) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token or "", encoding="utf-8")


def clear_token() -> None:
    try:
        TOKEN_FILE.unlink(missing_ok=True)
    except Exception:
        pass
