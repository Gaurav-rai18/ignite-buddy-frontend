"""`trainee-desktop`: the desktop assistant. A transparent always-on-top overlay (PySide6 + embedded Chromium) showing a 3D
character at the bottom-right; a global shortcut summons it to listen or to take typed input."""
import os
import sys

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from client import config
from .hotkey import GlobalHotkey
from .runtime import AgentRuntime
from .window import OverlayWindow


def make_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#2f5bea")); p.setPen(Qt.NoPen); p.drawEllipse(6, 6, 52, 52)
    p.setBrush(QColor("#f4f6fb")); p.drawEllipse(16, 14, 32, 28)
    p.setBrush(QColor("#141a2b")); p.drawRoundedRect(20, 22, 24, 12, 6, 6)
    p.setBrush(QColor("#4dd2ff")); p.drawEllipse(25, 26, 5, 5); p.drawEllipse(34, 26, 5, 5)
    p.end()
    return QIcon(pm)


class Bridge(QObject):
    """Messages from the page (via the agent thread) -> the Qt thread."""
    hit = Signal(list)
    hide = Signal()
    quit = Signal()
    active = Signal(bool)


class Shell:
    def __init__(self, app: QApplication, runtime: AgentRuntime, url: str):
        self.app, self.runtime, self.active = app, runtime, False
        self.window = OverlayWindow(url)
        self.bridge = Bridge()
        self.bridge.hit.connect(self.window.set_hit_rects)
        self.bridge.hide.connect(self.window.hide)
        self.bridge.quit.connect(self.quit)
        self.bridge.active.connect(lambda a: setattr(self, "active", a))
        runtime.agent.shell = self._from_page                           # called on the agent thread

        self.tray = QSystemTrayIcon(make_icon(), app)
        menu = QMenu()
        self.act_summon = QAction(f"Talk to the assistant  ({config.HOTKEY})", menu); self.act_summon.triggered.connect(self.summon)
        self.act_toggle = QAction("Show / hide the character", menu); self.act_toggle.triggered.connect(self.toggle_visible)
        act_quit = QAction("Quit", menu); act_quit.triggered.connect(self.quit)
        for a in (self.act_summon, self.act_toggle, act_quit):
            menu.addAction(a)
        self.tray.setContextMenu(menu); self.tray.setToolTip("Trainee Assistant")
        self.tray.activated.connect(lambda reason: self.summon() if reason == QSystemTrayIcon.Trigger else None)
        self.tray.show()

        self.hotkey = GlobalHotkey(config.HOTKEY)
        self.hotkey.activated.connect(self.summon)
        self.hotkey.failed.connect(lambda msg: self.tray.showMessage("Trainee Assistant", msg, QSystemTrayIcon.Warning, 8000))
        self.hotkey.start()

    # ---- from the page ----
    def _from_page(self, msg: dict):
        t = msg.get("type")
        if t == "shell_hit":
            self.bridge.hit.emit(msg.get("rects") or [])
        elif t == "shell_hide":
            self.bridge.hide.emit()
        elif t == "shell_quit":
            self.bridge.quit.emit()
        elif t == "shell_active":
            self.bridge.active.emit(bool(msg.get("active")))

    # ---- actions ----
    def summon(self):
        """Global shortcut handler acting as a toggle between show and hide.

        If the assistant is currently visible and active, pressing the hotkey hides
        the window and deactivates the agent. If the window is hidden or inactive,
        it brings the overlay to the front, reveals it, and triggers activation.
        """
        if self.window.isVisible() and self.active:
            self.window.hide()
            self.active = False
            self.runtime.agent.push_shell("deactivate")
        else:
            self.window.bring_to_front()
            self.active = True
            self.runtime.agent.push_shell("activate")

    def toggle_visible(self):
        """Toggles assistant window visibility via tray menu or shortcut."""
        self.summon()

    def quit(self):
        self.hotkey.stop()
        self.tray.hide()
        self.runtime.stop()
        self.app.quit()


def main():
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Trainee Assistant")
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("[desktop] no system tray here; use the shortcut or click the character.")
    runtime = AgentRuntime()
    url = runtime.start()
    shell = Shell(app, runtime, url)
    shell.window.show()
    print(f"[desktop] running. Shortcut: {config.HOTKEY}   (UI at {url})", flush=True)
    code = app.exec()
    runtime.stop()
    sys.exit(code)


if __name__ == "__main__":
    main()
