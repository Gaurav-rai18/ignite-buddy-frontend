"""
Activity recorder, one per user. The CLIENT samples the active window and sends it; this class applies the user's
own privacy rules, merges identical consecutive samples into one row (start_ts..end_ts) and enforces pause /
assessment-block / retention. Timestamps are the SERVER's clock (a client cannot forge or skew them).
Masking/redaction happens BEFORE anything is written.
"""
import json
import threading
import time

from server import config
from server.domain import policy
from shared import redaction
from shared import protocol as P

OWNER_GRACE = 30.0      # seconds a device "owns" a user's tracking after its last accepted sample


class ActivityRecorder:
    def __init__(self, store):
        self.store = store
        self._last = None
        self._owner = None            # connection id of the device currently feeding samples
        self._owner_seen = 0.0
        self._lock = threading.Lock()

    # ---------- pause / resume (persisted) ----------
    def pause(self, seconds=None):
        self.store.set_setting("tracking_paused_until", "inf" if seconds is None else time.time() + seconds)

    def resume(self):
        self.store.set_setting("tracking_paused_until", "0")

    def paused_until(self) -> float:
        return float(self.store.get_setting("tracking_paused_until", "0"))

    def is_paused(self, now=None) -> bool:
        return (now or time.time()) < self.paused_until()

    def pause_state(self, now=None) -> dict:
        """What the client needs to know to stop sampling: {paused, seconds|None}."""
        now = now or time.time()
        until = self.paused_until()
        if now >= until:
            return {"paused": False, "seconds": None}
        return {"paused": True, "seconds": None if until == float("inf") else until - now}

    def reset(self):
        with self._lock:
            self._last = None

    # ---------- user's private-app blocklist ----------
    def blocklist(self) -> list[str]:
        try:
            return [x.lower() for x in json.loads(self.store.get_setting("app_blocklist", "[]"))]
        except ValueError:
            return []

    # ---------- recording ----------
    def record_sample(self, ts: float, app: str, title: str, idle: bool):
        app, title = redaction.mask(app, title, self.blocklist())
        idle = 1 if idle else 0
        with self._lock, self.store.conn() as con:
            last = self._last
            contiguous = last is not None and ts - last["end"] <= config.ACTIVITY_INTERVAL * 3
            if contiguous and (last["app"], last["title"], last["idle"]) == (app, title, idle):
                con.execute("UPDATE activity_events SET end_ts=? WHERE id=?", (ts, last["id"]))
                last["end"] = ts
            else:
                if contiguous:                               # close the previous segment at the moment of change
                    con.execute("UPDATE activity_events SET end_ts=? WHERE id=?", (ts, last["id"]))
                new_id = con.insert("INSERT INTO activity_events(start_ts,end_ts,app,title,idle) VALUES (?,?,?,?,?)",
                                    (ts, ts, app, title, idle))
                self._last = {"id": new_id, "app": app, "title": title, "idle": idle, "end": ts}

    def ingest(self, app, title, idle, now=None, source=None) -> bool:
        """Entry point for one client sample. Returns True if it was recorded."""
        now = now or time.time()
        if self.is_paused(now) or (config.PAUSE_TRACKING_WHEN_BLOCKED and policy.is_blocked(self.store.user_id)):
            self._last = None
            return False
        if not isinstance(app, str) or not app.strip():       # lock screen / no focused window
            return False
        if source is not None:                                # several devices: only one feeds the timeline
            if self._owner not in (None, source) and now - self._owner_seen < OWNER_GRACE:
                return False
            self._owner, self._owner_seen = source, now
        self.record_sample(now, app[:P.MAX_APP_LEN], str(title or "")[:P.MAX_TITLE_LEN], bool(idle))
        return True

    def purge_old(self):
        """Retention: raw events older than RETENTION_DAYS are deleted. Summaries are kept."""
        cutoff = time.time() - config.RETENTION_DAYS * 86400
        with self.store.conn() as con:
            con.execute("DELETE FROM activity_events WHERE end_ts < ?", (cutoff,))
            con.execute("DELETE FROM screen_history WHERE ts < ?", (cutoff,))


_recorders: dict[str, ActivityRecorder] = {}
_lock = threading.Lock()


def recorder_for(store) -> ActivityRecorder:
    with _lock:
        r = _recorders.get(store.user_id)
        if r is None or r.store is not store:
            r = _recorders[store.user_id] = ActivityRecorder(store)
        return r
