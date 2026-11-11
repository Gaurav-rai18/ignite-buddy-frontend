import types
import pytest
from client.device import executor as ex
from client.device.executor import DeviceExecutor
from client.device.indexer import Index
from shared import protocol as P
from shared.redaction import mask, redact_screen


class L:
    def __init__(self): self.log = []
    def open_path(self, p): self.log.append(("open", p))
    def launch_app(self, p): self.log.append(("app", p))
    def which(self, e): return "/bin/" + e
    def spawn(self, a): self.log.append(("spawn", a))
    def run(self, argv, cwd, timeout): self.log.append(("run", argv)); return 0, "ok"
    def open_url(self, u): self.log.append(("url", u))


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(ex, "SCRIPT_EXT", {".bat", ".py", ".sh"})
    allowed, outside = tmp_path / "ok", tmp_path / "outside"
    (allowed / "proj a").mkdir(parents=True); (allowed / "proj b").mkdir(); outside.mkdir()
    (allowed / "proj a" / "run.sh").write_text("echo 1")
    (allowed / "tool.exe").write_text("x"); (outside / "secret.txt").write_text("s")
    cfg = types.SimpleNamespace(SEARCH_ROOTS=[allowed.resolve()], SCRIPT_ROOTS=[allowed.resolve()], SKIP_DIRS=set(),
                                MAX_DEPTH=4, SCRIPT_TIMEOUT=5, DOC_EXTS={".txt"}, MAX_DOC_BYTES=10**6,
                                MAX_DOCS_PER_FOLDER=10, MAX_FILE_BYTES=10**5,
                                WRITE_ROOTS=[allowed.resolve()], DEFAULT_PARENT=allowed.resolve(), HOME_DIR=allowed.resolve() / 'TraineeAssistant')
    idx = Index(cfg.SEARCH_ROOTS, cfg.SKIP_DIRS, 4); idx.refresh()
    lau, asked = L(), []
    e = DeviceExecutor(cfg, confirm=lambda t, p: asked.append(t) or True, launcher=lau, index=idx)
    return e, lau, asked, allowed, outside


def test_paths_outside_allowlist_are_refused(env):
    e, lau, _, allowed, outside = env
    for op, a in [("open_folder", {"path": str(outside)}), ("open_file", {"path": str(outside / "secret.txt")}),
                  ("open_folder", {"path": str(allowed / ".." / "outside")}), ("read_document", {"path": str(outside / "secret.txt")})]:
        assert e.handle(op, a).status == P.ERROR, op
    assert not lau.log


def test_executables_cannot_be_opened_and_unknown_ops_fail(env):
    e, lau, *_ = env
    assert e.handle("open_file", {"path": str(env[3] / "tool.exe")}).status == P.ERROR
    assert e.handle("format_disk", {}).status == P.ERROR
    assert e.handle("open_file", {"path": 5}).status == P.ERROR


def test_ambiguity_then_choice_validated_against_index(env):
    e, _, _, allowed, outside = env
    r = e.handle("find_folder", {"query": "proj"})
    assert r.status == P.AMBIGUOUS and len(r.options) == 2
    assert e.handle("find_folder", {"query": "proj", "choice": r.options[0]}).status == P.OK
    assert e.handle("find_folder", {"query": "proj", "choice": str(outside)}).status == P.ERROR   # not from our index


def test_run_file_needs_local_approval_and_detects_swap(env):
    e, lau, asked, allowed, _ = env
    d = str(allowed / "proj a")
    assert e.handle("run_file", {"file": "run.sh", "cwd": d}).status == P.OK and asked and any(x[0] == "run" for x in lau.log)
    lau.log.clear()
    e.confirm = lambda t, p: False
    assert e.handle("run_file", {"file": "run.sh", "cwd": d}).status == P.CANCELLED and not lau.log
    def swap(t, p): (allowed / "proj a" / "run.sh").write_text("rm -rf ~"); return True
    e.confirm = swap
    r = e.handle("run_file", {"file": "run.sh", "cwd": d})
    assert r.status == P.ERROR and "changed" in r.message and not lau.log


def test_run_file_rejects_paths_and_wrong_roots(env):
    e, _, _, allowed, outside = env
    assert e.handle("run_file", {"file": "../x.sh", "cwd": str(allowed)}).status == P.ERROR
    assert e.handle("run_file", {"file": "x.sh", "cwd": str(outside)}).status == P.ERROR


def test_open_target_cascade(env):
    e, lau, *_ = env
    assert e.handle("open_target", {"query": "proj a"}).status == P.OK and lau.log[-1][0] == "open"
    assert e.handle("open_target", {"query": "zzzz nothing"}).status == P.ERROR


def test_open_url_only_http(env):
    e, lau, *_ = env
    assert e.handle("open_url", {"url": "javascript:alert(1)"}).status == P.ERROR
    assert e.handle("open_url", {"url": "github.com"}).data["msg"].startswith("Opened https://github.com")


def test_redaction_and_masking():
    assert "[email]" in redact_screen("mail me a@b.com") and "[jwt]" in redact_screen("eyJabcdefgh.eyJabcdefgh.abcdefghij")
    assert mask("KeePass", "x") == ("(private)", "") and mask("Code", "Incognito tab") == ("(private)", "")
    assert mask("Code", "main.py")[1] == "main.py"


def test_sampler_masks_and_stops_when_paused():
    from client.sensors.activity import ActivitySampler
    sent = []
    probe = types.SimpleNamespace(active_window=lambda: ("KeePass", "vault"), idle_seconds=lambda: 0)
    cfg = types.SimpleNamespace(APP_BLOCKLIST=[], IDLE_AFTER=60, ACTIVITY_INTERVAL=5)
    s = ActivitySampler(sent.append, probe, cfg)
    assert not s.sample_once()                      # not connected
    s.connected = True
    assert s.sample_once() and sent[-1]["app"] == "(private)" and sent[-1]["title"] == ""
    s.set_tracking(True, None)
    n = len(sent)
    assert not s.sample_once() and len(sent) == n   # paused: nothing leaves the machine
    s.set_tracking(False); s.blocked = True
    assert not s.sample_once()
