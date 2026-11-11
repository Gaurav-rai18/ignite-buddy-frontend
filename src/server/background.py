"""Starts the server's background work (idempotent). Run it in ONE process only when scaling out."""
import threading

from server import config

_started = False


def start():
    global _started
    if _started or not config.RUN_BACKGROUND:
        return
    _started = True
    from server.jobs.runner import run_forever
    threading.Thread(target=run_forever, daemon=True, name="scheduler").start()
