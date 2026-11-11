"""Global keyboard shortcut listener for Windows virtual desktop environments (Accops VDI).

Uses the native Win32 `RegisterHotKey` API from user32.dll on a dedicated background thread.
This allows summoning or toggling the assistant overlay while another window or virtualized
application has input focus, without installing intrusive low-level keyboard hooks.
"""
import ctypes
import sys
import threading
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal

MODS = {"alt": 0x1, "ctrl": 0x2, "control": 0x2, "shift": 0x4, "win": 0x8, "meta": 0x8, "super": 0x8}
NAMED = {"space": 0x20, "enter": 0x0D, "return": 0x0D, "tab": 0x09, "esc": 0x1B, "escape": 0x1B, "backspace": 0x08,
         "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
         "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28}
MOD_NOREPEAT = 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012


def parse_hotkey(text: str) -> tuple[int, int]:
    """Parse a shortcut description string (e.g. 'ctrl+alt+space') into Win32 modifier flags and a virtual-key code.

    Requires at least one modifier key (Ctrl, Alt, Shift, or Win) alongside the primary key to ensure
    regular text typing is never intercepted by the global shortcut handler.
    """
    parts = [p.strip().lower() for p in text.replace(" ", "").split("+") if p.strip()]
    if len(parts) < 2:
        raise ValueError("a shortcut needs at least one modifier and a key, e.g. ctrl+alt+space")
    mods, key = 0, None
    for p in parts:
        if p in MODS:
            mods |= MODS[p]
        elif key is not None:
            raise ValueError(f"more than one key in '{text}'")
        elif p in NAMED:
            key = NAMED[p]
        elif len(p) == 1 and p.isalnum():
            key = ord(p.upper())
        elif p[0] == "f" and p[1:].isdigit() and 1 <= int(p[1:]) <= 24:
            key = 0x70 + int(p[1:]) - 1
        else:
            raise ValueError(f"unknown key '{p}'")
    if not mods or key is None:
        raise ValueError(f"'{text}' needs a modifier (ctrl/alt/shift/win) and one key")
    return mods, key


class GlobalHotkey(QObject):
    """Listens for a system-wide global hotkey to activate or toggle the assistant.

    Emits `activated` when the key combination is pressed, or `failed` if the shortcut
    is already reserved by another application or operating system shell.
    """
    activated = Signal()
    failed = Signal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text, self._thread, self._tid = text, None, None

    def start(self):
        """Parse shortcut text and initiate the background Windows message loop."""
        try:
            mods, vk = parse_hotkey(self.text)
        except ValueError as e:
            self.failed.emit(str(e))
            return
        if sys.platform == "win32":
            self._thread = threading.Thread(target=self._win_loop, args=(mods, vk), daemon=True, name="hotkey")
            self._thread.start()
        else:
            self._pynput()

    def _win_loop(self, mods: int, vk: int):
        """Native Windows event pump processing WM_HOTKEY messages on a dedicated background thread."""
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
        self._tid = kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, 1, mods | MOD_NOREPEAT, vk):
            self.failed.emit(f"The shortcut {self.text} is already used by another program. Set ASSISTANT_HOTKEY to something else.")
            return
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    self.activated.emit()
        finally:
            user32.UnregisterHotKey(None, 1)

    def _pynput(self):
        """Fallback listener for development environments when running on non-Windows platforms."""
        try:
            from pynput import keyboard
        except ImportError:
            self.failed.emit("Global shortcuts need Windows (or: pip install pynput). Use the tray icon or click the avatar.")
            return
        combo = "+".join(f"<{p}>" if len(p) > 1 and p not in ("space",) else (f"<{p}>" if p == "space" else p)
                         for p in self.text.lower().replace(" ", "").split("+"))
        self._listener = keyboard.GlobalHotKeys({combo: self.activated.emit})
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """Unregister the global shortcut and post WM_QUIT to terminate the background message pump."""
        if sys.platform == "win32" and self._tid:
            ctypes.windll.user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
        listener = getattr(self, "_listener", None)
        if listener:
            listener.stop()
