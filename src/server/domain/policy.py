"""Assessment policy. The SERVER owns it; clients only display it and fail closed.
DEV: in-memory flag (global, plus optional per-user override). PRODUCTION: back this with the admin service /
database. The model gateway should ALSO refuse model calls for blocked users, so a client-side bypass gains nothing.
"""
import os
import threading

_lock = threading.Lock()
_DEFAULT_REASON = "The assistant is disabled during the assessment."
_state = {"blocked": os.getenv("ASSISTANT_BLOCKED") == "1", "reason": _DEFAULT_REASON}
_user_blocked: dict[str, bool] = {}


def is_blocked(user_id: str | None = None) -> bool:
    with _lock:
        if _state["blocked"] or bool(user_id and _user_blocked.get(user_id)):
            return True

    # Check automated test lockdown from published schedule
    try:
        from server.apps.buddy_controller.test_lock import get_active_test_lock
        user_obj = None
        if user_id:
            from server.apps.accounts.models import User
            user_obj = User.objects.filter(id=user_id).select_related("sub_batch__batch").first()
        lock_info = get_active_test_lock(user=user_obj)
        if lock_info.get("is_locked"):
            return True
    except Exception:
        pass

    return False


def snapshot(user_id: str | None = None) -> dict:
    with _lock:
        if _state["blocked"] or bool(user_id and _user_blocked.get(user_id)):
            return {"blocked": True, "reason": _state["reason"]}

    # Check automated test lockdown from published schedule
    try:
        from server.apps.buddy_controller.test_lock import get_active_test_lock
        user_obj = None
        if user_id:
            from server.apps.accounts.models import User
            user_obj = User.objects.filter(id=user_id).select_related("sub_batch__batch").first()
        lock_info = get_active_test_lock(user=user_obj)
        if lock_info.get("is_locked"):
            return {
                "blocked": True,
                "reason": lock_info.get("reason", "Assessment in progress. Buddy assistant is automatically disabled."),
                "test_lock": lock_info,
            }
    except Exception:
        pass

    return {"blocked": False, "reason": _state["reason"]}


def set_blocked(flag: bool, reason: str | None = None, user_id: str | None = None):
    """user_id=None blocks/unblocks everyone; otherwise only that user (e.g. one batch taking an assessment)."""
    with _lock:
        if user_id:
            _user_blocked[user_id] = bool(flag)
        else:
            _state["blocked"] = bool(flag)
        if reason:
            _state["reason"] = reason


# ---------------------------------------------------------------------------------------------
# Admin capabilities: what an assistant account MAY do. Safe defaults; the admin widens or narrows them.
#   ASSISTANT_CAPABILITIES="files.delete=on,system.lock=off"           (global overrides)
#   ASSISTANT_POLICY_FILE=/etc/assistant/policy.json                    {"default": {...}, "users": {"alice": {...}}}
# Enforced on the SERVER before a step runs. (The client additionally enforces folder allowlists and confirmations.)
# ---------------------------------------------------------------------------------------------
import json  # noqa: E402

DEFAULT_CAPS = {
    "files.read": True, "files.create": True, "files.copy": True, "files.rename": True, "files.move": True,
    "files.delete": False,                     # destructive: off until an admin enables it (then: Recycle Bin + confirm)
    "scripts.run": True,                       # run .bat/.sh/.py inside allowed folders, after the user's approval
    "system.open": True,                       # Settings pages, Calculator, Task Manager, Clock...
    "system.lock": True, "clipboard.write": True,
    "kb.ignite": True, "kb.general": True,       # which knowledge-base spaces this account may search
    "native.schedule": True,                   # mirror reminders/timers into Windows Task Scheduler (toast + alarm sound)
}
_caps_lock = threading.Lock()
_global_caps: dict[str, bool] = {}
_user_caps: dict[str, dict[str, bool]] = {}


def _truthy(v) -> bool:
    return str(v).lower() in ("1", "on", "true", "yes", "enabled")


def load_capabilities():
    """(Re)read admin configuration from the environment / policy file."""
    with _caps_lock:
        _global_caps.clear()
        _user_caps.clear()
        for item in os.getenv("ASSISTANT_CAPABILITIES", "").split(","):
            if "=" in item:
                k, v = item.split("=", 1)
                _global_caps[k.strip()] = _truthy(v.strip())
        path = os.getenv("ASSISTANT_POLICY_FILE")
        if path and os.path.exists(path):
            data = json.load(open(path, encoding="utf-8"))
            _global_caps.update({k: bool(v) for k, v in data.get("default", {}).items()})
            for uid, caps in data.get("users", {}).items():
                _user_caps[uid] = {k: bool(v) for k, v in caps.items()}


def allows(cap: str, user_id: str | None = None) -> bool:
    with _caps_lock:
        if user_id and cap in _user_caps.get(user_id, {}):
            return _user_caps[user_id][cap]
        return _global_caps.get(cap, DEFAULT_CAPS.get(cap, False))      # unknown capability = denied


def set_capability(cap: str, flag: bool, user_id: str | None = None):
    with _caps_lock:
        (_user_caps.setdefault(user_id, {}) if user_id else _global_caps)[cap] = bool(flag)


def capabilities(user_id: str | None = None) -> dict[str, bool]:
    return {c: allows(c, user_id) for c in DEFAULT_CAPS}


load_capabilities()
