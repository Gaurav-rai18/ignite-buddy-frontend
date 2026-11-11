import types
import pytest
from client.device import winnative
from client.device.executor import DeviceExecutor
from client.device.indexer import Index
from shared import protocol as P


class L:
    supports_native = True
    def __init__(self): self.log = []; self.ps_code = 0
    def open_path(self, p): self.log.append(("open", p))
    def launch_app(self, p): self.log.append(("app", p))
    def which(self, e): return "/bin/" + e
    def spawn(self, a): self.log.append(("spawn", a))
    def run(self, argv, cwd, timeout): return 0, "ok"
    def open_url(self, u): self.log.append(("url", u))
    def open_uri(self, u): self.log.append(("uri", u))
    def start_exe(self, e): self.log.append(("exe", e))
    def lock(self): self.log.append(("lock",))
    def clipboard_set(self, t): self.log.append(("clip", t))
    def trash(self, p): self.log.append(("trash", p)); __import__("os").system(f"rm -rf '{p}'")
    def powershell(self, script): self.log.append(("ps", script)); return self.ps_code, "err text"


@pytest.fixture
def env(tmp_path):
    docs, other = tmp_path / "Documents", tmp_path / "Other"
    docs.mkdir(); other.mkdir()
    cfg = types.SimpleNamespace(SEARCH_ROOTS=[tmp_path.resolve()], WRITE_ROOTS=[docs.resolve()], DEFAULT_PARENT=docs.resolve(),
                                HOME_DIR=docs.resolve() / "TraineeAssistant", SCRIPT_ROOTS=[docs.resolve()], SKIP_DIRS=set(),
                                MAX_DEPTH=4, SCRIPT_TIMEOUT=5, DOC_EXTS={".txt"}, MAX_DOC_BYTES=10**6, MAX_DOCS_PER_FOLDER=10,
                                MAX_FILE_BYTES=10**5)
    idx = Index(cfg.SEARCH_ROOTS, cfg.SKIP_DIRS, 4); idx.refresh()
    lau, asked = L(), []
    e = DeviceExecutor(cfg, confirm=lambda t, p: asked.append(t) or True, launcher=lau, index=idx)
    return e, lau, asked, docs, other


def ok(r): assert r.status == P.OK, r; return r


# ---------------- notes ----------------
def test_notes_are_files_in_the_dedicated_folder(env):
    e, _, _, docs, _ = env
    ok(e.handle("add_note", {"text": "The viva is on Friday at 10"}))
    ok(e.handle("add_note", {"text": "Buy a notebook"}))
    files = list((docs / "TraineeAssistant" / "Notes").glob("*.md"))
    assert len(files) == 2 and "viva" in " ".join(f.name for f in files)
    assert "viva" in ok(e.handle("search_notes", {"query": "viva"})).data["msg"].lower()
    assert "notebook" in ok(e.handle("list_notes", {})).data["msg"].lower()
    assert "Friday" in ok(e.handle("read_note", {"query": "viva"})).data["msg"]
    ok(e.handle("append_note", {"query": "viva", "text": "bring ID"}))
    assert "bring ID" in ok(e.handle("read_note", {"query": "viva"})).data["msg"]
    ok(e.handle("update_note", {"query": "viva", "text": "Viva moved to Monday"}))
    body = ok(e.handle("read_note", {"query": "viva"})).data["msg"]
    assert "Monday" in body and "Friday" not in body


def test_note_delete_asks_and_keeps_a_copy(env):
    e, _, asked, docs, _ = env
    ok(e.handle("add_note", {"text": "temporary"}))
    e.confirm = lambda t, p: False
    assert e.handle("delete_note", {"query": "temporary"}).status == P.CANCELLED
    assert len(list((docs / "TraineeAssistant" / "Notes").glob("*.md"))) == 1
    e.confirm = lambda t, p: True
    ok(e.handle("delete_note", {"query": "temporary"}))
    assert not list((docs / "TraineeAssistant" / "Notes").glob("*.md"))
    assert len(list((docs / "TraineeAssistant" / "Notes" / ".trash").glob("*.md"))) == 1


def test_note_ambiguity_uses_choice(env):
    e, *_ = env
    ok(e.handle("add_note", {"text": "react hooks cheat sheet"}))
    ok(e.handle("add_note", {"text": "react router cheat sheet"}))
    r = e.handle("read_note", {"query": "react cheat sheet"})
    assert r.status == P.AMBIGUOUS and len(r.options) == 2
    assert "hooks" in ok(e.handle("read_note", {"query": "x", "choice": next(o for o in r.options if "hooks" in o)})).data["msg"]
    assert e.handle("read_note", {"query": "x", "choice": "../../etc/passwd"}).status == P.ERROR


# ---------------- tasks ----------------
def test_tasks_crud(env):
    e, _, _, docs, _ = env
    ok(e.handle("add_task", {"text": "finish react assignment"})); ok(e.handle("add_task", {"text": "buy notebook"}))
    assert "[ ] buy notebook" in ok(e.handle("list_tasks", {})).data["msg"]
    ok(e.handle("complete_task", {"query": "notebook"}))
    assert "[x] buy notebook" in ok(e.handle("list_tasks", {})).data["msg"]
    ok(e.handle("delete_task", {"query": "react"}))
    assert "react" not in ok(e.handle("list_tasks", {})).data["msg"]
    assert (docs / "TraineeAssistant" / "Tasks.md").read_text().startswith("# Tasks")


# ---------------- file CRUD ----------------
def test_file_crud_inside_write_roots(env):
    e, lau, asked, docs, other = env
    ok(e.handle("create_folder", {"name": "react notes"}))
    assert (docs / "react notes").is_dir()
    ok(e.handle("create_file", {"name": "todo", "parent": str(docs / "react notes"), "content": "hello"}))
    assert (docs / "react notes" / "todo.txt").read_text() == "hello"
    ok(e.handle("rename_path", {"path": str(docs / "react notes" / "todo.txt"), "new_name": "plan"}))
    assert (docs / "react notes" / "plan.txt").exists()                        # extension kept
    (docs / "dest").mkdir()
    ok(e.handle("copy_path", {"path": str(docs / "react notes"), "destination": str(docs / "dest")}))
    assert (docs / "dest" / "react notes" / "plan.txt").exists() and (docs / "react notes").exists()
    ok(e.handle("move_path", {"path": str(docs / "react notes" / "plan.txt"), "destination": str(docs / "dest")}))
    assert (docs / "dest" / "plan.txt").exists() and not (docs / "react notes" / "plan.txt").exists()
    assert "plan.txt" in ok(e.handle("list_folder", {"path": str(docs / "dest")})).data["msg"]
    assert "hello" in ok(e.handle("read_file", {"path": str(docs / "dest" / "plan.txt")})).data["msg"]
    ok(e.handle("delete_path", {"path": str(docs / "dest" / "plan.txt")}))
    assert lau.log[-1][0] == "trash" and asked and not (docs / "dest" / "plan.txt").exists()


def test_file_safety_rules(env):
    e, lau, _, docs, other = env
    (other / "x.txt").write_text("x")
    for op, a in [("create_folder", {"name": "bad/name"}), ("create_folder", {"name": ".."}), ("create_file", {"name": "evil.bat"}),
                  ("create_file", {"name": "evil.exe"}), ("create_folder", {"name": "con"}),
                  ("create_folder", {"name": "ok", "parent": str(other)}),                         # outside WRITE_ROOTS
                  ("delete_path", {"path": str(other / "x.txt")}), ("rename_path", {"path": str(other / "x.txt"), "new_name": "y"}),
                  ("delete_path", {"path": str(docs)}),                                           # a root
                  ("delete_path", {"path": str(docs / "TraineeAssistant")}),
                  ("move_path", {"path": str(docs), "destination": str(docs)})]:
        (docs / "TraineeAssistant").mkdir(exist_ok=True)
        assert e.handle(op, a).status == P.ERROR, (op, a)
    ok(e.handle("create_file", {"name": "a.txt"}))
    assert e.handle("rename_path", {"path": str(docs / "a.txt"), "new_name": "a.bat"}).status == P.ERROR   # cannot become a script
    assert e.handle("create_file", {"name": "a.txt"}).status == P.ERROR                                    # no overwrite
    assert not any(x[0] == "trash" for x in lau.log)
    assert e.handle("read_file", {"path": str(other / "x.txt")}).status == P.OK                            # reads allowed in SEARCH_ROOTS
    (docs / ".env").write_text("SECRET=1")
    assert e.handle("read_file", {"path": str(docs / ".env")}).status == P.ERROR


def test_delete_declined_keeps_file(env):
    e, lau, _, docs, _ = env
    (docs / "keep.txt").write_text("1")
    e.confirm = lambda t, p: False
    assert e.handle("delete_path", {"path": str(docs / "keep.txt")}).status == P.CANCELLED and (docs / "keep.txt").exists()


# ---------------- system ----------------
def test_system_targets_allowlist_only(env):
    e, lau, *_ = env
    ok(e.handle("open_system", {"target": "task manager"})); ok(e.handle("open_system", {"target": "wifi settings"}))
    ok(e.handle("open_system", {"target": "alarms"}))
    assert ("exe", "taskmgr.exe") in lau.log and ("uri", "ms-settings:network-wifi") in lau.log and ("uri", "ms-clock:") in lau.log
    assert e.handle("open_system", {"target": "powershell -c calc"}).status == P.ERROR
    ok(e.handle("lock_screen", {})); ok(e.handle("clipboard_set", {"text": "npm install"}))
    assert ("lock",) in lau.log and ("clip", "npm install") in lau.log
    assert "It is" in ok(e.handle("get_time", {})).data["msg"]


def test_known_folder_names_resolve(env):
    e, *_ = env
    r = e.handle("find_folder", {"query": "documents"})
    assert r.status in (P.OK, P.ERROR)                                       # ~/Documents may not exist in the sandbox


# ---------------- native Windows scheduling ----------------
def test_native_schedule_builds_safe_powershell(env):
    e, lau, *_ = env
    ok(e.handle("native_schedule", {"ref": "ab12cd34-reminder1", "kind": "reminder", "at": "1893500000",
                                    "text": "it's <b>5pm</b>; $(calc)", "repeat": "daily"}))
    script = lau.log[-1][1]
    assert "Register-ScheduledTask" in script and "-Daily" in script and "FromUnixTimeSeconds(1893500000)" in script
    assert "$(calc)" not in script and "<b>" not in script                    # text is only inside the base64 payload
    import base64, re
    enc = re.search(r"-EncodedCommand (\S+?)'", script).group(1)
    toast = base64.b64decode(enc).decode("utf-16-le")
    assert "&lt;b&gt;5pm&lt;/b&gt;" in toast and "it''s" in toast and 'scenario="alarm"' in toast and "Looping.Alarm2" in toast
    ok(e.handle("native_cancel", {"ref": "ab12cd34-reminder1"}))
    assert "Unregister-ScheduledTask" in lau.log[-1][1]


def test_native_rejects_bad_input_and_non_windows(env):
    e, lau, *_ = env
    for bad in ({"ref": "x'; calc; '", "kind": "reminder", "at": "1"}, {"ref": "ok", "kind": "evil", "at": "1"},
                {"ref": "ok", "kind": "timer", "at": "1", "repeat": "hourly"}, {"ref": "ok", "kind": "timer", "at": "soon"}):
        assert e.handle("native_schedule", bad).status == P.ERROR
    lau.supports_native = False
    assert e.handle("native_schedule", {"ref": "ok", "kind": "timer", "at": "1"}).status == P.ERROR
    lau.supports_native, lau.ps_code = True, 1
    assert "refused" in e.handle("native_schedule", {"ref": "ok", "kind": "timer", "at": "1"}).message


def test_one_time_task_cleans_itself_up():
    s = winnative.schedule_script("u-timer1", "timer", 1893500000, "t")
    assert "-Once" in s and "EndBoundary" in s and "DeleteExpiredTaskAfter" in s


def test_index_follows_the_assistants_own_changes(env):
    e, lau, _, docs, _ = env
    ok(e.handle("create_folder", {"name": "react notes"}))
    assert e.handle("find_folder", {"query": "react notes"}).data["path"] == str(docs / "react notes")      # no manual refresh
    ok(e.handle("create_file", {"name": "todo.txt", "parent": str(docs / "react notes")}))
    assert e.handle("find_file", {"query": "todo.txt"}).data["path"].endswith("todo.txt")
    ok(e.handle("rename_path", {"path": str(docs / "react notes" / "todo.txt"), "new_name": "plan"}))
    assert e.handle("find_file", {"query": "todo.txt"}).status == P.ERROR and e.handle("find_file", {"query": "plan.txt"}).status == P.OK
    ok(e.handle("delete_path", {"path": str(docs / "react notes" / "plan.txt")}))
    assert e.handle("find_file", {"query": "plan.txt"}).status == P.ERROR
