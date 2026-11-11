"""Unified desktop entry: pick Electron or PySide6 at runtime.

Environment
-----------
ASSISTANT_SHELL
    ``auto`` (default) | ``electron`` | ``pyside6`` | ``qt``

    auto
        Prefer Electron when ``desktop-electron/node_modules/electron`` is
        available (or a global ``electron`` on PATH) *and* Node can run it.
        Otherwise use PySide6.

Why two shells?
---------------
Both host the same React UI and the same Python agent. Only the OS chrome
differs (window, tray, hotkey, click-through).

* **PySide6** — pure Python install; good for locked-down corporate images
  that already ship Qt or allow ``pip install PySide6``.
* **Electron** — familiar to web teams; ``npm run dist`` produces installers
  (NSIS / AppImage / dmg). Requires Node for build and a larger runtime.

Usage
-----
    trainee-desktop              # auto
    ASSISTANT_SHELL=electron trainee-desktop
    ASSISTANT_SHELL=pyside6  trainee-desktop
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    # src/client/shell/launcher.py → repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def _electron_dir() -> Path:
    env = os.getenv("ASSISTANT_ELECTRON_DIR")
    if env:
        return Path(env)
    return _repo_root() / "desktop-electron"


def electron_available() -> bool:
    """True when we can launch the Electron shell."""
    ed = _electron_dir()
    main_js = ed / "main.js"
    if not main_js.is_file():
        return False
    # local electron binary from npm install
    local = ed / "node_modules" / ".bin" / ("electron.cmd" if os.name == "nt" else "electron")
    if local.is_file() or local.exists():
        return True
    return shutil.which("electron") is not None


def pyside6_available() -> bool:
    try:
        import PySide6  # noqa: F401
        return True
    except Exception:
        return False


def choose_shell(preference: str | None = None) -> str:
    pref = (preference or os.getenv("ASSISTANT_SHELL") or "auto").strip().lower()
    if pref in ("qt", "pyside", "pyside6"):
        return "pyside6"
    if pref == "electron":
        return "electron"
    # auto
    if electron_available():
        return "electron"
    return "pyside6"


def run_electron() -> int:
    ed = _electron_dir()
    local = ed / "node_modules" / ".bin" / ("electron.cmd" if os.name == "nt" else "electron")
    electron = str(local) if local.exists() else "electron"
    if not electron_available():
        print(
            "[desktop] Electron shell requested but not available.\n"
            "  cd desktop-electron && npm install\n"
            "  Or set ASSISTANT_SHELL=pyside6",
            file=sys.stderr,
        )
        return 1
    env = os.environ.copy()
    # Ensure the agent module is importable when Electron spawns it
    src = str(_repo_root() / "src")
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [src, env.get("PYTHONPATH", "")]))
    print(f"[desktop] shell=electron  ({ed})", flush=True)
    return subprocess.call([electron, str(ed)], env=env, cwd=str(ed))


def run_pyside6() -> int:
    if not pyside6_available():
        print(
            "[desktop] PySide6 shell requested but PySide6 is not installed.\n"
            "  pip install -e \".[desktop]\"\n"
            "  Or install Electron: cd desktop-electron && npm install\n"
            "  then ASSISTANT_SHELL=electron trainee-desktop",
            file=sys.stderr,
        )
        return 1
    print("[desktop] shell=pyside6", flush=True)
    from client.desktop.qt.app import main as qt_main
    qt_main()
    return 0


def main(argv: list[str] | None = None) -> None:
    # Optional: trainee-desktop --shell electron
    args = list(argv if argv is not None else sys.argv[1:])
    pref = None
    if "--shell" in args:
        i = args.index("--shell")
        if i + 1 < len(args):
            pref = args[i + 1]
            del args[i : i + 2]
    shell = choose_shell(pref)
    code = run_electron() if shell == "electron" else run_pyside6()
    raise SystemExit(code)


if __name__ == "__main__":
    main()


def main_electron() -> None:
    """Console entry that always selects Electron."""
    os.environ["ASSISTANT_SHELL"] = "electron"
    main()


def main_qt() -> None:
    """Console entry that always selects PySide6."""
    os.environ["ASSISTANT_SHELL"] = "pyside6"
    main()
