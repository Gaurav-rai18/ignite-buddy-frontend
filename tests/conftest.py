import os
import tempfile
import uuid

_tmp = tempfile.mkdtemp(prefix="assistant_test_")
os.environ.update({"ASSISTANT_DATA": _tmp, "ASSISTANT_DEBUG": "1", "ASSISTANT_DISABLE_BACKGROUND": "1",
                   "ASSISTANT_TOKENS": "tokA:alice,tokB:bob", "ASSISTANT_ADMIN_TOKEN": "admin-secret", "ASSISTANT_LOCAL_DB": os.path.join(_tmp, "local_client.db"), "ASSISTANT_TOKEN": "dev-token",
                   "DJANGO_SETTINGS_MODULE": "server.ignite_server.settings"})
import django  # noqa: E402

django.setup()
from django.core.management import call_command
try:
    call_command("migrate", verbosity=0)
except Exception:
    pass

import pytest  # noqa: E402
from server.domain.session import Session, User  # noqa: E402
from shared import protocol as P  # noqa: E402


class FakeUI:
    """Records everything; answers confirm/choose/device_call from scripted values."""
    def __init__(self, approve=True, choice=None, device=None):
        self.said, self.tokens, self.pushed, self.calls = [], [], [], []
        self.approve, self.choice = approve, choice
        self.device = device or (lambda op, args: P.DeviceResult.error('no device in this test'))
    def state(self, s): pass
    def say(self, t): self.said.append(t)
    def token(self, t): self.tokens.append(t)
    def end_message(self): pass
    def push(self, m): self.pushed.append(m)
    def confirm(self, title, preview=""): self.said.append(f"CONFIRM:{title}"); return self.approve
    def choose(self, q, options): return self.choice
    def capture_screen(self): return None
    def device_call(self, op, args):
        self.calls.append((op, args))
        return self.device(op, args)


@pytest.fixture
def make_session():
    def make(**kw):
        return Session.create(User(id=f"user_{uuid.uuid4().hex}", name="t"), FakeUI(**kw))
    return make


@pytest.fixture
def session(make_session):
    return make_session()
