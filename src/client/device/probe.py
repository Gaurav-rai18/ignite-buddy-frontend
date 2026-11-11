"""
Active-window + idle-time probes per OS. Returns (app, title) or (None, None).
Windows uses ctypes + psutil (no admin needed). macOS needs Accessibility permission for the terminal/app.
Linux needs X11 + xdotool (+ xprintidle); Wayland is not supported.
In the Electron build, replace this with the `active-win` package in the main process.
"""
import ctypes
import os
import shutil
import subprocess
import sys


def active_window():
    try:
        if sys.platform == "win32":
            return _win_active()
        if sys.platform == "darwin":
            return _mac_active()
        return _linux_active()
    except Exception:
        return None, None


def idle_seconds() -> float:
    try:
        if sys.platform == "win32":
            return _win_idle()
        if sys.platform == "darwin":
            return _mac_idle()
        return _linux_idle()
    except Exception:
        return 0.0


# ---------------- Windows ----------------
def _win_active():
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, None
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        import psutil
        app = os.path.splitext(psutil.Process(pid.value).name())[0]
    except Exception:
        app = "unknown"
    return app, buf.value


def _win_idle():
    from ctypes import wintypes

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(info)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    return ((ctypes.windll.kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0


# ---------------- macOS ----------------
_MAC_SCRIPT = '''tell application "System Events"
set p to first application process whose frontmost is true
set n to name of p
try
set t to name of front window of p
on error
set t to ""
end try
end tell
return n & "|||" & t'''


def _mac_active():
    out = subprocess.run(["osascript", "-e", _MAC_SCRIPT], capture_output=True, text=True, timeout=3).stdout
    app, _, title = out.strip().partition("|||")
    return (app or None), title


def _mac_idle():
    out = subprocess.run(["ioreg", "-c", "IOHIDSystem"], capture_output=True, text=True, timeout=3).stdout
    for line in out.splitlines():
        if "HIDIdleTime" in line:
            return int(line.split("=")[-1].strip()) / 1e9
    return 0.0


# ---------------- Linux (X11) ----------------
def _linux_active():
    if not shutil.which("xdotool"):
        return None, None
    wid = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=3).stdout.strip()
    if not wid:
        return None, None
    title = subprocess.run(["xdotool", "getwindowname", wid], capture_output=True, text=True, timeout=3).stdout.strip()
    pid = subprocess.run(["xdotool", "getwindowpid", wid], capture_output=True, text=True, timeout=3).stdout.strip()
    app = "unknown"
    if pid.isdigit():
        try:
            app = open(f"/proc/{pid}/comm").read().strip()
        except OSError:
            pass
    return app, title


def _linux_idle():
    if not shutil.which("xprintidle"):
        return 0.0
    return int(subprocess.run(["xprintidle"], capture_output=True, text=True, timeout=3).stdout.strip() or 0) / 1000.0
