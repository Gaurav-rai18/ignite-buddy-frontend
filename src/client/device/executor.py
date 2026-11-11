"""
Device executor: performs server-requested operations ON THIS MACHINE.

The server is NOT trusted to be safe for this machine, so the client enforces its own rules:
  - every path must be inside SEARCH_ROOTS (scripts: SCRIPT_ROOTS), after symlink resolution
  - run_file always asks the USER here (confirm callback) and re-checks the script's hash right before running
  - only the fixed operation set in shared.protocol exists; there is no "run this string" operation
"""
import hashlib
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

from client import config as default_config
from shared import protocol as P
from shared.codectx import SENSITIVE_FILE, filename_from_title
from shared.protocol import DeviceResult
from shared.redaction import redact_screen
from . import winnative
from .errors import Ambiguity, Declined, DeviceError
from .fileops import FileOps
from .indexer import Index
from .launcher import SystemLauncher
from .localops import LocalOps
from client.localdb import LocalDB
from .systemtargets import ALIASES, TARGETS
from .vault import Vault


EDITORS = {"vscode": "code", "vs code": "code", "visual studio code": "code", "code": "code", "notepad": "notepad"}
BAD_OPEN = {".bat", ".cmd", ".ps1", ".exe", ".msi", ".sh", ".vbs", ".js"}
SCRIPT_EXT = {".bat", ".cmd", ".py"} if sys.platform == "win32" else {".sh", ".py"}


def _under(p: Path, roots) -> bool:
    return any(r == p or r in p.parents for r in roots)


class DeviceExecutor:
    def __init__(self, cfg=default_config, confirm=lambda title, preview: False, launcher=None, index=None, db=None):
        self.cfg, self.confirm = cfg, confirm
        self.launcher = launcher or SystemLauncher()
        self.index = index or Index(cfg.SEARCH_ROOTS, cfg.SKIP_DIRS, cfg.MAX_DEPTH)
        confirm_fn = lambda title, preview: self.confirm(title, preview)       # noqa: E731  (late-bound: tests swap self.confirm)
        self.vault = Vault(cfg.HOME_DIR, confirm_fn)
        self.files = FileOps(cfg, self.launcher, confirm_fn, protected=self.vault.protected())
        self.db = db or LocalDB(getattr(cfg, "LOCAL_DB", default_config.LOCAL_DB))
        self.local = LocalOps(self.db, confirm_fn)
        self.ops = {**self.files.ops(), **self.vault.ops(), **self.local.ops()}

    # ---------------- entry point ----------------
    def handle(self, op: str, args: dict) -> DeviceResult:
        fn = (self.ops.get(op) or getattr(self, f"op_{op}", None)) if op in P.DEVICE_OPS else None
        if fn is None:
            return DeviceResult.error(f"Unsupported operation: {op}")
        if not isinstance(args, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in args.items()):
            return DeviceResult.error("Malformed arguments")
        res = self._run(fn, op, args)
        if op not in ("chat_context", "show_audit") and res.status != P.AMBIGUOUS:     # reading the log is not an event
            try:
                self.db.audit(op, args, res.status, res.message)
            except Exception:
                pass
        return res

    def _run(self, fn, op, args) -> DeviceResult:
        try:
            data = fn(args)
            self._sync_index(op, args, data)
            return DeviceResult.ok(**data)
        except Ambiguity as a:
            return DeviceResult.ambiguous(a.question, a.options)
        except Declined:
            return DeviceResult.cancelled()
        except DeviceError as e:
            return DeviceResult.error(str(e))
        except Exception as e:                                   # never let one bad call kill the client
            return DeviceResult.error(f"{type(e).__name__}: {e}")

    def _sync_index(self, op, args, data):
        """After the assistant creates/renames/moves/copies/deletes something, the next command in the same sentence
        (or the next sentence) must already be able to find it."""
        new, old = data.get("path"), args.get("path")
        if op in ("create_folder", "create_file", "copy_path") and new:
            self.index.add_path(new)
            if op == "copy_path" and Path(new).is_dir():
                self.index.refresh_async()
        elif op in ("rename_path", "move_path") and new and old:
            self.index.remove_path(old)
            self.index.add_path(new)
            if Path(new).is_dir():
                self.index.refresh_async()
        elif op == "delete_path" and old:
            self.index.remove_path(old)

    # ---------------- safety helpers ----------------
    def _existing(self, path: str) -> Path:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            raise DeviceError(f"Path does not exist: {p}")
        allowed = list(self.cfg.SEARCH_ROOTS)
        if hasattr(self.cfg, "WRITE_ROOTS"):
            allowed.extend(self.cfg.WRITE_ROOTS)
        if hasattr(self.cfg, "HOME_DIR"):
            allowed.append(self.cfg.HOME_DIR)
        allowed.append(Path.cwd().resolve())
        if not _under(p, allowed):
            raise DeviceError(f"{p} is outside the allowed folders")
        return p

    def _resolve(self, query: str, kind: str, choice: str | None) -> str:
        if choice:                                                # a pick the user made among OUR options
            if not self.index.contains(choice):
                try:
                    cand = Path(choice).expanduser().resolve()
                    if cand.exists() and _under(cand, self.cfg.SEARCH_ROOTS):
                        return str(cand)
                except Exception:
                    pass
                raise DeviceError("That choice is not in the file index")
            return choice
        cleaned = query.strip('"\'')
        try:
            cand = Path(cleaned).expanduser().resolve()
            if cand.exists() and _under(cand, self.cfg.SEARCH_ROOTS):
                if kind == "dir" and cand.is_dir():
                    return str(cand)
                elif kind == "file" and cand.is_file():
                    return str(cand)
                elif kind == "any":
                    return str(cand)
        except Exception:
            pass
        hits = self.index.search(query, kind)
        if not hits or hits[0][1] < 60:
            raise DeviceError(f"No {'folder' if kind == 'dir' else 'file'} found matching '{query}'")
        best = hits[0][1]
        close = [h for h in hits if h[1] >= best - 5]
        if len(close) > 1 or best < 80:
            raise Ambiguity(f"Which one did you mean for '{query}'?", [h[0] for h in (close if len(close) > 1 else hits)])
        return hits[0][0]

    # ---------------- resolvers ----------------
    def _known_folder(self, query: str):
        t = TARGETS.get(ALIASES.get(query.strip().lower(), query.strip().lower()))
        if t and t[0] == "folder" and Path(t[1]).is_dir() and _under(Path(t[1]).resolve(), self.cfg.SEARCH_ROOTS):
            return t[1]
        return None

    def op_find_folder(self, a):
        p = self._known_folder(a["query"]) or self._resolve(a["query"], "dir", a.get("choice"))
        return {"path": p, "name": Path(p).name, "parent": str(Path(p).parent), "msg": f"Found folder {p}"}

    def op_find_file(self, a):
        p = self._resolve(a["query"], "file", a.get("choice"))
        return {"path": p, "name": Path(p).name, "parent": str(Path(p).parent), "msg": f"Found file {p}"}

    # ---------------- open things ----------------
    def op_open_app(self, a):
        hits = self.index.find_app(a["name"])
        if not hits or hits[0][2] < 70:
            raise DeviceError(f"App '{a['name']}' not found")
        self.launcher.launch_app(hits[0][0])
        return {"msg": f"Opened {hits[0][1]}"}

    def op_open_in_app(self, a):
        exe = EDITORS.get(a["app"].lower().strip())
        if not exe:
            raise DeviceError(f"Unsupported editor '{a['app']}'")
        full = self.launcher.which(exe)
        if not full:
            raise DeviceError(f"'{exe}' is not on PATH")
        p = self._existing(a["path"])
        self.launcher.spawn([full, str(p)])
        return {"msg": f"Opened {p.name} in {a['app']}"}

    def op_open_folder(self, a):
        p = self._existing(a["path"])
        self.launcher.open_path(str(p))
        return {"msg": f"Opened folder {p}"}

    def op_list_folder(self, a):
        """List contents of a folder, delegating to the file operations handler."""
        return self.files.op_list_folder(a)

    def op_open_file(self, a):
        p = self._existing(a["path"])
        if p.suffix.lower() in BAD_OPEN:
            raise DeviceError("Executable files cannot be opened this way. Use run.")
        self.launcher.open_path(str(p))
        return {"msg": f"Opened {p.name}"}

    def op_open_target(self, a):
        """'open X': an app if one matches well, else a folder, else a file."""
        q, choice = a["query"], a.get("choice")
        known = self._known_folder(q)
        if known and not choice:
            return self.op_open_folder({"path": known})
        if choice:
            kind = "dir" if Path(choice).is_dir() else "file"
            return (self.op_open_folder if kind == "dir" else self.op_open_file)({"path": choice})
        cleaned = q.strip('"\'')
        try:
            cand = Path(cleaned).expanduser().resolve()
            if cand.exists() and _under(cand, self.cfg.SEARCH_ROOTS):
                return (self.op_open_folder if cand.is_dir() else self.op_open_file)({"path": str(cand)})
        except Exception:
            pass
        apps = self.index.find_app(q)
        if apps and apps[0][2] >= 85:
            return self.op_open_app({"name": q})
        hits = self.index.search(q, "any")
        if not hits or hits[0][1] < 60:
            if apps and apps[0][2] >= 70:
                return self.op_open_app({"name": q})
            raise DeviceError(f"I couldn't find an app, folder or file matching '{q}'")
        best = hits[0][1]
        close = [h for h in hits if h[1] >= best - 5]
        if len(close) > 1 or best < 80:
            raise Ambiguity(f"Which one did you mean for '{q}'?", [h[0] for h in (close if len(close) > 1 else hits)])
        p = hits[0][0]
        return (self.op_open_folder if Path(p).is_dir() else self.op_open_file)({"path": p})

    def op_open_url(self, a):
        url = a["url"].strip()
        if re.match(r"^[a-z][a-z0-9+.-]*:(?!//|\d)", url, re.I):         # javascript:, file:, data: ... (not host:port)
            raise DeviceError("Only http/https URLs are allowed")
        if "://" not in url:
            url = "https://" + url
        if not url.lower().startswith(("http://", "https://")):
            raise DeviceError("Only http/https URLs are allowed")
        self.launcher.open_url(url)
        return {"msg": f"Opened {url}"}

    def op_web_search(self, a):
        self.launcher.open_url("https://www.google.com/search?q=" + quote_plus(a["query"]))
        return {"msg": f"Searched for '{a['query']}'"}

    # ---------------- run a script (user approves HERE) ----------------
    def _script_target(self, file: str, cwd: str):
        if Path(file).name != file:
            raise DeviceError("The script must be a bare file name, not a path")
        c = Path(cwd).expanduser().resolve()
        if not _under(c, self.cfg.SCRIPT_ROOTS):
            raise DeviceError(f"Scripts may only run inside: {', '.join(map(str, self.cfg.SCRIPT_ROOTS))}")
        f = c / file
        if not f.is_file():
            raise DeviceError(f"{file} not found in {c}")
        if f.suffix.lower() not in SCRIPT_EXT:
            raise DeviceError(f"Script type {f.suffix} is not allowed")
        return c, f

    def op_run_file(self, a):
        c, f = self._script_target(a["file"], a["cwd"])
        lines = f.read_text(errors="ignore").splitlines()[:15]
        preview = "\n".join(lines) + ("\n..." if len(lines) == 15 else "")
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if not self.confirm(f"Run `{a['file']}` in `{c}`", preview):
            raise Declined
        if hashlib.sha256(f.read_bytes()).hexdigest() != digest:          # swapped after approval?
            raise DeviceError("The script changed after you approved it. Nothing was run.")
        argv = ([sys.executable, str(f)] if f.suffix.lower() == ".py"
                else ["cmd.exe", "/c", str(f)] if sys.platform == "win32" else ["bash", str(f)])
        try:
            code, tail = self.launcher.run(argv, str(c), self.cfg.SCRIPT_TIMEOUT)
        except TimeoutError:
            raise DeviceError(f"{a['file']} timed out after {self.cfg.SCRIPT_TIMEOUT}s")
        except Exception as e:
            if type(e).__name__ == "TimeoutExpired":
                raise DeviceError(f"{a['file']} timed out after {self.cfg.SCRIPT_TIMEOUT}s")
            raise
        tail = tail[-1500:]
        if code != 0:
            raise DeviceError(f"{a['file']} exited with code {code}\n{tail}")
        return {"msg": f"{a['file']} finished (exit code 0)\n{tail}"}

    # ---------------- code helper: the open file ----------------
    def op_read_open_file(self, a):
        title = a.get("title", "")
        name = filename_from_title(title)
        if not name or SENSITIVE_FILE.search(name):
            return {"name": None}
        paths = self.index.by_name(name)
        if len(paths) > 1:                                    # 'main.py - my-project - Visual Studio Code'
            segs = [s.strip().lower() for s in re.split(r"\s[-\u2013\u2014\u2022]\s", title)[1:-1] if s.strip()]
            paths = [p for p in paths if any(seg in p.lower() for seg in segs)]
        if len(paths) != 1:
            return {"name": None}
        p = Path(paths[0]).resolve()
        if not _under(p, self.cfg.SEARCH_ROOTS) or p.stat().st_size > self.cfg.MAX_FILE_BYTES:
            return {"name": None}
        line = int(a["line"]) if a.get("line", "").isdigit() else None
        lines = p.read_text(errors="ignore").splitlines()
        lo, hi = ((max(0, line - 26), min(len(lines), line + 25)) if line and 1 <= line <= len(lines)
                  else (0, min(len(lines), 120)))
        snippet = redact_screen("\n".join(f"{i + 1}: {lines[i]}" for i in range(lo, hi)))
        return {"name": p.name, "snippet": snippet}

    # ---------------- documents for /index ----------------
    def op_list_documents(self, a):
        folder = Path(a["folder"]).expanduser().resolve()
        if not folder.is_dir() or not _under(folder, self.cfg.SEARCH_ROOTS):
            raise DeviceError("That folder does not exist or is outside the allowed folders")
        files = []
        for dp, dns, fns in os.walk(folder):
            dns[:] = [d for d in dns if d not in self.cfg.SKIP_DIRS and not d.startswith(".")]
            for n in fns:
                p = Path(dp) / n
                if p.suffix.lower() in self.cfg.DOC_EXTS and not SENSITIVE_FILE.search(n):
                    try:
                        if p.stat().st_size <= self.cfg.MAX_DOC_BYTES:
                            files.append({"path": str(p), "hash": hashlib.sha1(p.read_bytes()).hexdigest()})
                    except OSError:
                        pass
                if len(files) >= self.cfg.MAX_DOCS_PER_FOLDER:
                    break
        return {"files": files, "msg": f"{len(files)} documents"}

    def op_read_document(self, a):
        p = self._existing(a["path"])
        if p.suffix.lower() not in self.cfg.DOC_EXTS or SENSITIVE_FILE.search(p.name):
            raise DeviceError("That file type is not allowed")
        if p.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            pages = [[i + 1, (pg.extract_text() or "")] for i, pg in enumerate(PdfReader(str(p)).pages)]
        else:
            pages = [[1, p.read_text(errors="ignore")]]
        return {"pages": [[n, redact_screen(t, 200000)] for n, t in pages if t.strip()], "msg": p.name}

    def op_refresh_index(self, a):
        r = self.index.refresh()
        return {**r, "msg": f"Indexed {r['files']} files and {r['apps']} apps"}

    # ---------------- notes folder, clock, system ----------------
    def op_open_notes_folder(self, a):
        self.vault.notes.mkdir(parents=True, exist_ok=True)
        self.launcher.open_path(str(self.vault.notes))
        return {"path": str(self.vault.notes), "msg": f"Opened {self.vault.notes}"}

    def op_get_time(self, a):
        return {"msg": time.strftime("It is %A, %d %B %Y, %I:%M %p.")}

    def op_open_system(self, a):
        key = a["target"].strip().lower()
        kind, value = TARGETS.get(ALIASES.get(key, key), (None, None))
        if not kind:
            raise DeviceError(f"I don't know how to open '{a['target']}'.")
        try:
            if kind == "folder":
                self.launcher.open_path(value)
            elif kind == "uri":
                self.launcher.open_uri(value)
            else:
                self.launcher.start_exe(value)
        except OSError as e:
            raise DeviceError(str(e))
        return {"msg": f"Opened {a['target']}"}

    def op_lock_screen(self, a):
        self.launcher.lock()
        return {"msg": "Locking your computer."}

    def op_clipboard_set(self, a):
        text = a["text"]
        if len(text) > 20000:
            raise DeviceError("That text is too long.")
        try:
            self.launcher.clipboard_set(text)
        except Exception as e:
            raise DeviceError(f"Could not use the clipboard ({type(e).__name__}).")
        return {"msg": "Copied to the clipboard."}

    # ---------------- native Windows scheduling (Task Scheduler + toast) ----------------
    def _native(self):
        if not getattr(self.launcher, "supports_native", False):
            raise DeviceError("Native scheduling is available on Windows only.")

    def op_native_schedule(self, a):
        self._native()
        try:
            script = winnative.schedule_script(a["ref"], a["kind"], int(float(a["at"])), a.get("text", ""), a.get("repeat", ""))
        except (ValueError, KeyError) as e:
            raise DeviceError(f"Invalid schedule request ({e}).")
        code, out = self.launcher.powershell(script)
        if code:
            raise DeviceError("Windows Task Scheduler refused it: " + out.strip()[:200])
        return {"msg": "Scheduled in Windows."}

    def op_native_cancel(self, a):
        self._native()
        try:
            script = winnative.cancel_script(a["ref"])
        except ValueError:
            raise DeviceError("Invalid reference.")
        self.launcher.powershell(script)
        return {"msg": "Removed from Windows."}
