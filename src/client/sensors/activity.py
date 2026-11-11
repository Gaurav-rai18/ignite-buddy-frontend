"""
Activity sampler. Every few seconds: read the active window, MASK private windows + redact the title ON THIS
MACHINE, and send one small message to the server. Stops completely while tracking is paused or the assessment
policy blocks the assistant, so nothing leaves the machine in those states.
"""
import threading
import time

from client import config
from client.device import probe
from shared import redaction


class ActivitySampler:
    def __init__(self, send, probe_mod=probe, cfg=config):
        self.send, self.probe, self.cfg = send, probe_mod, cfg
        self.paused_until = 0.0            # local monotonic-ish deadline derived from the server's `seconds`
        self.blocked = False
        self.connected = False
        self._stop = False

    # state pushed by the server
    def set_tracking(self, paused: bool, seconds=None):
        self.paused_until = 0.0 if not paused else (float("inf") if seconds is None else time.time() + seconds)

    def active(self) -> bool:
        return self.connected and not self.blocked and time.time() >= self.paused_until

    def sample_once(self) -> bool:
        if not self.active():
            return False
        app, title = self.probe.active_window()
        if not app:
            return False
        app, title = redaction.mask(app, title, self.cfg.APP_BLOCKLIST)
        idle = self.probe.idle_seconds() > self.cfg.IDLE_AFTER
        self.send({"type": "activity_sample", "app": app, "title": title, "idle": idle})
        return True

    def start(self):
        def loop():
            while not self._stop:
                try:
                    self.sample_once()
                except Exception:
                    pass
                time.sleep(self.cfg.ACTIVITY_INTERVAL)
        threading.Thread(target=loop, daemon=True, name="activity").start()

    def stop(self):
        self._stop = True
