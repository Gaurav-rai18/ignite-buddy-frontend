"""The overlay window: frameless, transparent, always on top, no taskbar entry, anchored to the bottom-right corner,
and click-through everywhere except where the page says something is drawn."""
import os
import sys

from PySide6.QtCore import QRect, QUrl, Qt
from PySide6.QtGui import QColor, QRegion
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

from .mask import normalize_rects


class LockedPage(QWebEnginePage):
    """The assistant never navigates away and never opens windows; the microphone is granted to ITS OWN page only."""
    def __init__(self, parent, origin_prefix: str):
        super().__init__(parent)
        self.origin_prefix = origin_prefix
        if hasattr(self, "permissionRequested"):                       # Qt >= 6.8
            self.permissionRequested.connect(self._on_permission)
        elif hasattr(self, "featurePermissionRequested"):              # older Qt 6
            self.featurePermissionRequested.connect(self._on_feature)

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        return url.toString().startswith(self.origin_prefix)

    def createWindow(self, window_type):
        return None

    def _mic_ok(self, origin: QUrl) -> bool:
        return origin.toString().rstrip("/").startswith(self.origin_prefix.rstrip("/"))

    def _on_permission(self, permission):
        kinds = getattr(type(permission), "PermissionType", None)
        audio = getattr(kinds, "MediaAudioCapture", None)
        if self._mic_ok(permission.origin()) and permission.permissionType() == audio:
            permission.grant()
        else:
            permission.deny()

    def _on_feature(self, origin, feature):
        ok = self._mic_ok(origin) and feature == QWebEnginePage.Feature.MediaAudioCapture
        policy = QWebEnginePage.PermissionPolicy.PermissionGrantedByUser if ok else QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
        self.setFeaturePermission(origin, feature, policy)


class OverlayWindow(QWebEngineView):
    SIZE = (780, 860)

    def __init__(self, url: str, size=None):
        super().__init__()
        self.url = url
        self.size_wh = size or self.SIZE
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setContextMenuPolicy(Qt.NoContextMenu)
        page = LockedPage(self, url.rsplit("/", 1)[0] if url.endswith("/") else url)
        page.setBackgroundColor(QColor(Qt.transparent))
        s = page.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)      # the "copy" buttons
        s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)       # spoken answers
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.setPage(page)
        self.resize(*self.size_wh)
        self.anchor()
        self.setMask(QRegion(0, 0, 1, 1))
        self.setUrl(QUrl(url))

    def anchor(self, screen=None):
        """Covers the usable screen area so top-middle and bottom-right elements can be rendered seamlessly."""
        screen = screen or self.screen() or self.window().screen()
        geo: QRect = screen.availableGeometry()
        self.setGeometry(geo.x(), geo.y(), geo.width(), geo.height())

    def set_hit_rects(self, rects):
        """Everything outside these rectangles is transparent AND lets clicks reach the programs underneath."""
        region = QRegion()
        for x, y, w, h in normalize_rects(rects, self.width(), self.height()):
            region = region.united(QRegion(x, y, w, h))
        if region.isEmpty():
            region = QRegion(self.width() - 2, self.height() - 2, 1, 1)
        self.setMask(region)

    def bring_to_front(self):
        self.show()
        self.raise_()
        self.activateWindow()
        if sys.platform == "win32":                                     # Windows refuses focus to background apps; the hotkey press allows it
            try:
                import ctypes
                ctypes.windll.user32.SetForegroundWindow(int(self.winId()))
            except Exception:
                pass
        self.setFocus()
