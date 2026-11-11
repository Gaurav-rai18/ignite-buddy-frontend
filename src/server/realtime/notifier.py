"""Lets background threads (scheduler, views) push a message to devices via the channel layer
without deadlocks on Windows or sync/async context mismatches."""
import asyncio
import hashlib
import threading

from channels.layers import get_channel_layer


def user_group(user_id: str) -> str:
    return "u_" + hashlib.sha256(user_id.encode()).hexdigest()[:32]       # group names must be short + ASCII


ALL_GROUP = "all_trainees"


def batch_group(batch: str) -> str:
    clean = str(batch or "").strip()
    return "b_" + hashlib.sha256(clean.encode()).hexdigest()[:32]


def _safe_send_group(group: str, message: dict) -> bool:
    layer = get_channel_layer()
    if layer is None:
        return False
    try:
        cur_loop = asyncio.get_running_loop()
    except RuntimeError:
        cur_loop = None

    if cur_loop and cur_loop.is_running():
        cur_loop.create_task(layer.group_send(group, message))
        return True

    def _worker():
        try:
            async def _send():
                await layer.group_send(group, message)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(asyncio.wait_for(_send(), timeout=1.0))
            loop.close()
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return True


def push(user_id: str, msg: dict) -> bool:
    return _safe_send_group(user_group(user_id), {"type": "push.message", "msg": msg})


def sync_batch(batch: str) -> bool:
    """Tell every connected PC of a batch (or all PCs for "*") that the admin published something new."""
    target_group = ALL_GROUP if str(batch).strip().lower() in ("*", "all", "") else batch_group(batch)
    return _safe_send_group(target_group, {"type": "sync.push"})


def broadcast_batch(batch: str, text: str, kind: str = "broadcast") -> bool:
    """Send an active real-time notification to a specific batch or all trainees."""
    target_group = ALL_GROUP if str(batch).strip().lower() in ("*", "all", "") else batch_group(batch)
    return _safe_send_group(target_group, {
        "type": "trainee.notification",
        "kind": kind,
        "text": text,
    })
