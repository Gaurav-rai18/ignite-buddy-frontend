"""Per-connection state handed to every service. Nothing below the transport layer knows about WebSockets.

`ui` is the transport adapter (see transport/session_ui.py). Services only use this surface:
    ui.state(s) ui.say(text) ui.token(text) ui.end_message() ui.push(msg)
    ui.confirm(title, preview) -> bool          ask the user to approve a SERVER-side risky action
    ui.choose(question, options) -> str|None    ask the user to pick one of several matches
    ui.capture_screen() -> dict|None            ask the client for a screenshot (the user previews/approves it)
    ui.device_call(op, args) -> DeviceResult    run an operation ON the client machine
"""
from dataclasses import dataclass, field

from server.data.store import Store, get_store


class Cancelled(Exception):
    """The user pressed cancel / the connection dropped / an assessment block started."""


@dataclass(frozen=True)
class User:
    id: str
    name: str = ""
    role: str = "trainee"
    batch: str = "default"
    account_user_id: int | None = None


@dataclass
class Session:
    user: User
    ui: object
    store: Store
    history: list = field(default_factory=list)       # chat turns, current connection only (never persisted)

    @classmethod
    def create(cls, user: User, ui) -> "Session":
        return cls(user=user, ui=ui, store=get_store(user.id))

    @property
    def device(self):
        return self.ui
