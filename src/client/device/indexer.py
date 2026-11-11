"""File and app indexes, IN MEMORY on the client. Names of the user's files never leave this machine."""
import os
import re
import sys
import threading
import time
from pathlib import Path

from rapidfuzz import fuzz, process

ALIASES = {"vs code": "code", "vscode": "code", "visual studio code": "code",
           "chrome": "google chrome", "edge": "microsoft edge"}


def norm(s: str) -> str:
    return re.sub(r"[\W_]+", " ", s.lower()).strip()


def build_app_index() -> dict[str, str]:
    apps = {}
    if sys.platform == "win32":
        for base in (r"%ProgramData%\Microsoft\Windows\Start Menu\Programs",
                     r"%AppData%\Microsoft\Windows\Start Menu\Programs"):
            for p in Path(os.path.expandvars(base)).rglob("*.lnk"):
                apps[norm(p.stem)] = str(p)
    elif sys.platform == "darwin":
        for p in Path("/Applications").glob("*.app"):
            apps[norm(p.stem)] = str(p)
    else:
        for d in ("/usr/share/applications", str(Path.home() / ".local/share/applications")):
            for p in Path(d).glob("*.desktop"):
                apps[norm(p.stem)] = str(p)
    return apps


class Index:
    def __init__(self, search_roots, skip_dirs, max_depth):
        self.roots, self.skip, self.depth = list(search_roots), set(skip_dirs), max_depth
        self.apps: dict[str, str] = {}
        self.files: list[tuple] = []            # (path, name, norm, is_dir, mtime)
        self._lock = threading.Lock()

    def refresh(self) -> dict:
        apps = build_app_index()
        rows = []
        for root in self.roots:
            if not root.exists():
                continue
            base = len(root.parts)
            for dp, dns, fns in os.walk(root):
                dns[:] = [d for d in dns if d not in self.skip and not d.startswith(".")]
                dirs = list(dns)
                if len(Path(dp).parts) - base >= self.depth:
                    dns[:] = []
                for n, is_dir in [(d, 1) for d in dirs] + [(f, 0) for f in fns]:
                    p = os.path.join(dp, n)
                    try:
                        rows.append((p, n, norm(n), is_dir, os.path.getmtime(p)))
                    except OSError:
                        pass
        with self._lock:
            self.apps, self.files = apps, rows
        return {"apps": len(apps), "files": len(rows)}

    def find_app(self, name: str, limit=3):
        q = ALIASES.get(norm(name), norm(name))
        if not self.apps:
            return []
        return [(self.apps[k], k, int(s)) for k, s, _ in process.extract(q, list(self.apps), scorer=fuzz.WRatio, limit=limit)]

    def search(self, query: str, kind: str = "any", limit=3):
        """kind: 'dir' | 'file' | 'any'. -> [(path, score)] best first."""
        with self._lock:
            rows = [r for r in self.files if kind == "any" or (kind == "dir") == bool(r[3])]
        if not rows:
            return []
        hits = process.extract(norm(query), [r[2] for r in rows], scorer=fuzz.WRatio, limit=limit * 3)
        month = time.time() - 30 * 86400
        scored = [(rows[i][0], int(s) + (3 if rows[i][4] > month else 0)) for _, s, i in hits]
        scored.sort(key=lambda x: -x[1])
        return scored[:limit]

    def by_name(self, name: str) -> list[str]:
        with self._lock:
            return [r[0] for r in self.files if not r[3] and r[1].lower() == name.lower()]

    def contains(self, path: str) -> bool:
        with self._lock:
            return any(r[0] == path for r in self.files)

    # ---- keep the index current after the assistant itself changes files ----
    def add_path(self, path: str):
        try:
            p = Path(path)
            row = (str(p), p.name, norm(p.name), 1 if p.is_dir() else 0, os.path.getmtime(p))
        except OSError:
            return
        with self._lock:
            self.files = [r for r in self.files if r[0] != row[0]] + [row]

    def remove_path(self, path: str):
        prefix = str(path)
        with self._lock:
            self.files = [r for r in self.files if r[0] != prefix and not r[0].startswith(prefix + os.sep)]

    def refresh_async(self):
        if not getattr(self, "_refreshing", False):
            self._refreshing = True

            def work():
                try:
                    self.refresh()
                finally:
                    self._refreshing = False
            threading.Thread(target=work, daemon=True).start()
