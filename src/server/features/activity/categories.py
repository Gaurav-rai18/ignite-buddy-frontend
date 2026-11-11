"""Heuristic app/title -> category. Central admin can later override this mapping per organisation."""
import re

TERMINAL_EXACT = {"cmd", "wt", "bash", "zsh", "conhost"}
TERMINAL_SUB = ("powershell", "pwsh", "terminal", "iterm", "konsole", "xterm")
CODING_EXACT = {"code", "vim", "nvim", "idea", "cursor"}
CODING_SUB = ("pycharm", "webstorm", "devenv", "sublime", "notepad++", "eclipse", "studio", "vscode",
              "intellij", "clion", "rider", "insiders")
BROWSER_SUB = ("chrome", "msedge", "edge", "firefox", "brave", "opera", "safari", "vivaldi")
COMM_SUB = ("teams", "slack", "outlook", "zoom", "discord", "thunderbird", "mail", "skype", "webex",
            "whatsapp", "telegram")
DOC_SUB = ("winword", "word", "excel", "powerpnt", "powerpoint", "acrobat", "acrord", "soffice",
           "libreoffice", "onenote", "notion", "sumatrapdf", "foxit")

DISTRACT = re.compile(r"youtube|netflix|facebook|instagram|twitter|reddit|tiktok|prime video|hotstar|"
                      r"spotify|twitch|9gag|whatsapp web", re.I)
LEARNING = re.compile(r"tutorial|course|lecture|learn|how to|explained|crash course|documentation", re.I)
RESEARCH = re.compile(r"stack ?overflow|github|gitlab|docs|documentation|mdn|geeksforgeeks|w3schools|python|"
                      r"django|react|javascript|tutorial|api reference|npm|pypi|developer\.|learn", re.I)

FOCUS = {"coding", "terminal", "research", "documents"}

# spoken name -> substring of the process name the OS reports
APP_ALIASES = {"vs code": "code", "vscode": "code", "visual studio code": "code", "visual studio": "devenv",
               "chrome": "chrome", "google chrome": "chrome", "edge": "msedge", "microsoft edge": "msedge",
               "word": "winword", "powerpoint": "powerpnt", "terminal": "terminal", "command prompt": "cmd"}
CATEGORIES = {"coding", "terminal", "research", "browsing", "communication", "documents", "distraction", "other"}


def categorize(app: str, title: str = "") -> str:
    a, t = (app or "").lower(), title or ""
    if a == "(private)":
        return "private"
    if a in TERMINAL_EXACT or any(s in a for s in TERMINAL_SUB):
        return "terminal"
    if a in CODING_EXACT or any(s in a for s in CODING_SUB):
        return "coding"
    if any(s in a for s in BROWSER_SUB):
        if DISTRACT.search(t):
            return "research" if LEARNING.search(t) else "distraction"
        return "research" if RESEARCH.search(t) else "browsing"
    if any(s in a for s in COMM_SUB):
        return "communication"
    if any(s in a for s in DOC_SUB):
        return "documents"
    return "other"
