"""Fixed allowlist of built-in Windows things the assistant may open. The server sends only a NAME from this table;
no free-form command, URI or path ever reaches the OS from here."""
from pathlib import Path

HOME = Path.home()
# name -> (kind, value).  kind: exe (Popen), uri (shell open), folder
TARGETS = {
    # built-in apps
    "calculator": ("exe", "calc.exe"), "notepad": ("exe", "notepad.exe"), "paint": ("exe", "mspaint.exe"),
    "task manager": ("exe", "taskmgr.exe"), "command prompt": ("exe", "cmd.exe"), "terminal": ("exe", "wt.exe"),
    "file explorer": ("exe", "explorer.exe"), "snipping tool": ("uri", "ms-screenclip:"),
    "clock": ("uri", "ms-clock:"), "calendar": ("uri", "outlookcal:"), "camera": ("uri", "microsoft.windows.camera:"),
    # Settings pages
    "wifi settings": ("uri", "ms-settings:network-wifi"), "network settings": ("uri", "ms-settings:network-status"),
    "bluetooth settings": ("uri", "ms-settings:bluetooth"), "display settings": ("uri", "ms-settings:display"),
    "sound settings": ("uri", "ms-settings:sound"), "battery settings": ("uri", "ms-settings:batterysaver"),
    "storage settings": ("uri", "ms-settings:storagesense"), "windows update settings": ("uri", "ms-settings:windowsupdate"),
    "apps settings": ("uri", "ms-settings:appsfeatures"), "privacy settings": ("uri", "ms-settings:privacy"),
    "time settings": ("uri", "ms-settings:dateandtime"),
    # well-known folders
    "downloads": ("folder", str(HOME / "Downloads")), "documents": ("folder", str(HOME / "Documents")),
    "desktop": ("folder", str(HOME / "Desktop")),
}
ALIASES = {"calc": "calculator", "cmd": "command prompt", "explorer": "file explorer", "screenshot tool": "snipping tool",
           "alarms": "clock", "alarm": "clock", "alarms app": "clock", "clock app": "clock", "wi-fi settings": "wifi settings",
           "date and time settings": "time settings", "update settings": "windows update settings"}
