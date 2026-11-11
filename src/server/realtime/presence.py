"""Which users have at least one open connection. In-process (single server process).
Scale-out: replace with a Redis set + heartbeat; the scheduler only needs `user_ids()`."""
import threading
from collections import Counter

_lock = threading.Lock()
_conns: Counter = Counter()


def add(user_id: str):
    with _lock:
        _conns[user_id] += 1


def remove(user_id: str):
    with _lock:
        _conns[user_id] -= 1
        if _conns[user_id] <= 0:
            del _conns[user_id]


def user_ids() -> list[str]:
    with _lock:
        return list(_conns)


def count(user_id: str | None = None) -> int:
    with _lock:
        return _conns[user_id] if user_id else sum(_conns.values())
