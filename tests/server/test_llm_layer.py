"""The LangChain/Ollama layer (gateway path, auth header, proxy, TLS, error messages) is checked by a script that
needs its own environment before `config` is imported, so it runs in a fresh interpreter."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_llm_layer_script():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    r = subprocess.run([sys.executable, str(ROOT / "tests/server/llm_layer_script.py")], env=env,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
