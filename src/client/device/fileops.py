"""
File CRUD on the trainee's PC. Every operation is confined to WRITE_ROOTS (reads: SEARCH_ROOTS), after symlink
resolution; roots themselves and the assistant's own folders can never be renamed/moved/deleted; executables cannot be
created; deletion always asks the user and goes to the Recycle Bin. The server's admin policy decides WHETHER a
trainee may use an operation; this class decides whether the operation is SAFE on this machine.
"""
import os
import re
import shutil
from pathlib import Path

from shared.codectx import SENSITIVE_FILE
from shared.redaction import redact_screen
from .errors import DeviceError, Declined

BLOCK_EXT = {".exe", ".msi", ".dll", ".scr", ".com", ".vbs", ".ps1", ".bat", ".cmd", ".lnk", ".reg", ".jar", ".sys"}
TEXT_EXT = {".txt", ".md", ".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".html", ".css", ".json", ".csv",
            ".sql", ".yml", ".yaml", ".xml", ".log", ".ini", ".toml", ".sh", ".bat", ".cmd", ".ipynb"}
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def under(p: Path, roots) -> bool:
    return any(r == p or r in p.parents for r in roots)


class FileOps:
    def __init__(self, cfg, launcher, confirm, protected=()):
        self.cfg, self.launcher, self.confirm = cfg, launcher, confirm
        self.protected = [Path(x).resolve() for x in (*cfg.SEARCH_ROOTS, *cfg.WRITE_ROOTS, *protected)]

    # ---------------- validation ----------------
    @staticmethod
    def clean_name(name: str, *, allow_blocked=False) -> str:
        name = (name or "").strip().strip(".")
        if not name or len(name) > 100 or BAD_CHARS.search(name) or name in (".", "..") or Path(name).stem.lower() in RESERVED:
            raise DeviceError(f"'{name}' is not a valid file or folder name.")
        if not allow_blocked and Path(name).suffix.lower() in BLOCK_EXT:
            raise DeviceError(f"For safety I can't create or rename to {Path(name).suffix} files.")
        return name

    def _existing(self, path: str, roots) -> Path:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            raise DeviceError(f"Path does not exist: {p}")
        allowed = list(roots)
        if hasattr(self.cfg, "WRITE_ROOTS"):
            allowed.extend(self.cfg.WRITE_ROOTS)
        if hasattr(self.cfg, "HOME_DIR"):
            allowed.append(self.cfg.HOME_DIR)
        allowed.append(Path.cwd().resolve())
        if not under(p, allowed):
            raise DeviceError(f"{p} is outside the allowed folders")
        return p

    def _writable(self, path: str) -> Path:
        return self._existing(path, self.cfg.WRITE_ROOTS)

    def _movable(self, path: str) -> Path:
        p = self._writable(path)
        if p in self.protected:
            raise DeviceError("That folder is protected and cannot be renamed, moved or deleted.")
        return p

    def _dest_dir(self, path: str | None) -> Path:
        d = Path(path).expanduser().resolve() if path else Path(self.cfg.DEFAULT_PARENT).resolve()
        if not d.is_dir() or not under(d, self.cfg.WRITE_ROOTS):
            raise DeviceError(f"{d} is not a folder I may write to")
        return d

    # ---------------- operations ----------------
    def op_create_folder(self, a):
        name = self.clean_name(a["name"])
        p = self._dest_dir(a.get("parent")) / name
        if p.exists():
            raise DeviceError(f"{p} already exists")
        p.mkdir()
        return {"path": str(p), "msg": f"Created folder {p}"}

    def op_create_file(self, a):
        name = self.clean_name(a["name"])
        if not Path(name).suffix:
            name += ".txt"
        content = a.get("content", "")
        if len(content) > 100_000:
            raise DeviceError("That content is too long.")
        p = self._dest_dir(a.get("parent")) / name
        if p.exists():
            raise DeviceError(f"{p} already exists")
        p.write_text(content, encoding="utf-8")
        return {"path": str(p), "msg": f"Created file {p}"}

    def op_rename_path(self, a):
        p = self._movable(a["path"])
        new = self.clean_name(a["new_name"])
        if p.is_file() and not Path(new).suffix:
            new += p.suffix                                   # "rename report.docx to final" keeps .docx
        target = p.with_name(new)
        if target.exists():
            raise DeviceError(f"{target.name} already exists")
        p.rename(target)
        return {"path": str(target), "msg": f"Renamed {p.name} to {target.name}"}

    def op_move_path(self, a):
        p, d = self._movable(a["path"]), self._dest_dir(a["destination"])
        if d == p or p in d.parents:
            raise DeviceError("A folder cannot be moved into itself")
        target = d / p.name
        if target.exists():
            raise DeviceError(f"{target} already exists")
        shutil.move(str(p), str(target))
        return {"path": str(target), "msg": f"Moved {p.name} to {d}"}

    def op_copy_path(self, a):
        p, d = self._existing(a["path"], self.cfg.SEARCH_ROOTS), self._dest_dir(a["destination"])
        target = d / p.name
        if target.exists():
            raise DeviceError(f"{target} already exists")
        if p.is_dir():
            if p in d.parents or d == p:
                raise DeviceError("A folder cannot be copied into itself")
            shutil.copytree(p, target)
        else:
            shutil.copy2(p, target)
        return {"path": str(target), "msg": f"Copied {p.name} to {d}"}

    def op_delete_path(self, a):
        p = self._movable(a["path"])
        if p.is_dir():
            n = sum(len(f) + len(d) for _, d, f in os.walk(p))
            what = f"Folder with {n} items"
        else:
            what = f"File, {p.stat().st_size / 1024:.1f} KB"
        if not self.confirm(f"Move to the Recycle Bin: {p.name}?", f"{p}\n{what}"):
            raise Declined
        self.launcher.trash(str(p))
        return {"msg": f"Moved {p.name} to the Recycle Bin"}

    def op_read_file(self, a):
        p = self._existing(a["path"], self.cfg.SEARCH_ROOTS)
        if not p.is_file() or p.suffix.lower() not in TEXT_EXT or SENSITIVE_FILE.search(p.name):
            raise DeviceError("I can only read ordinary text/code files.")
        if p.stat().st_size > self.cfg.MAX_FILE_BYTES:
            raise DeviceError("That file is too large to show here.")
        return {"msg": f"{p.name}:\n" + redact_screen(p.read_text(errors="ignore"), 3000), "path": str(p)}

    def op_list_folder(self, a):
        """Lists files and folders inside the target directory, gathering direct items and recursive tree entries."""
        p = self._existing(a["path"], self.cfg.SEARCH_ROOTS)
        if not p.is_dir():
            raise DeviceError(f"{p.name} is not a folder")

        # Determine parent folder path if within allowed search roots
        parent_path = None
        try:
            allowed = list(self.cfg.SEARCH_ROOTS)
            if hasattr(self.cfg, "WRITE_ROOTS"):
                allowed.extend(self.cfg.WRITE_ROOTS)
            if hasattr(self.cfg, "HOME_DIR"):
                allowed.append(self.cfg.HOME_DIR)
            allowed.append(Path.cwd().resolve())
            if p.parent != p and under(p.parent, allowed):
                parent_path = str(p.parent)
        except Exception:
            parent_path = None

        # 1. Direct children for standard non-recursive browsing
        direct_entries = sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        items = []
        for e in direct_entries:
            if e.name.startswith("."):
                continue
            try:
                is_dir = e.is_dir()
                size = e.stat().st_size if not is_dir else 0
            except Exception:
                is_dir = False
                size = 0
            items.append({
                "name": e.name,
                "is_dir": is_dir,
                "path": str(e),
                "rel_path": e.name,
                "parent_dir": "",
                "ext": e.suffix.lstrip(".").lower() if not is_dir else "folder",
                "size": size,
                "depth": 0,
            })
            if len(items) >= 200:
                break

        # 2. Recursive exploration for searching nested folders and files
        skip_dirs = getattr(self.cfg, "SKIP_DIRS", {"node_modules", ".git", "__pycache__", ".venv", "venv", "AppData", "$RECYCLE.BIN"})
        max_depth = getattr(self.cfg, "MAX_DEPTH", 5)
        max_recursive = 500
        recursive_items = []

        try:
            for root, dirs, files in os.walk(p):
                root_path = Path(root)
                try:
                    rel_to_root = root_path.relative_to(p)
                    cur_depth = len(rel_to_root.parts)
                except ValueError:
                    cur_depth = 0

                # Prune skip directories in-place
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith(".") and d not in skip_dirs
                ]
                if cur_depth >= max_depth:
                    dirs.clear()

                # Add subfolder entry (skip the root folder itself)
                if root_path != p:
                    recursive_items.append({
                        "name": root_path.name,
                        "is_dir": True,
                        "path": str(root_path),
                        "rel_path": str(rel_to_root).replace("\\", "/"),
                        "parent_dir": str(rel_to_root.parent).replace("\\", "/") if rel_to_root.parent != Path(".") else "",
                        "ext": "folder",
                        "size": 0,
                        "depth": cur_depth,
                    })
                    if len(recursive_items) >= max_recursive:
                        break

                # Add files in this directory level
                for fname in sorted(files, key=str.lower):
                    if fname.startswith("."):
                        continue
                    file_path = root_path / fname
                    try:
                        file_rel = file_path.relative_to(p)
                        size = file_path.stat().st_size
                    except Exception:
                        size = 0
                        file_rel = Path(fname)

                    recursive_items.append({
                        "name": fname,
                        "is_dir": False,
                        "path": str(file_path),
                        "rel_path": str(file_rel).replace("\\", "/"),
                        "parent_dir": str(file_rel.parent).replace("\\", "/") if file_rel.parent != Path(".") else "",
                        "ext": file_path.suffix.lstrip(".").lower() or "file",
                        "size": size,
                        "depth": cur_depth,
                    })
                    if len(recursive_items) >= max_recursive:
                        break

                if len(recursive_items) >= max_recursive:
                    break
        except Exception:
            pass

        if not items and not recursive_items:
            return {
                "msg": f"{p.name} is empty.",
                "folder": p.name,
                "path": str(p),
                "parent_path": parent_path,
                "items": [],
                "recursive_items": [],
            }

        return {
            "msg": f"Found {len(items)} items in {p.name}",
            "folder": p.name,
            "path": str(p),
            "parent_path": parent_path,
            "items": items,
            "recursive_items": recursive_items,
        }

    def ops(self):
        return {n[3:]: getattr(self, n) for n in dir(self) if n.startswith("op_")}
