"""Transparency + control: show what is stored about the user, and wipe it all."""
from datetime import datetime

from server import config
from server.knowledge.personal import PersonalVectors
from server.features.activity.recorder import recorder_for
from ..model import CONFIRM, SAFE
from ..parser import rule
from ..registry import tool

# (table, label, time column). Table names come from this constant list only.
TABLES = [("reminders", "Reminders", None), ("timers", "Timers", None),
          ("activity_events", "Activity records", "start_ts"), ("summaries", "Daily/session summaries", "created"),
          ("screen_history", "Screen-help history (question + answer only)", "ts"),
          ("actions", "Executed-action log", None)]


def _fmt(ts):
    """Format a POSIX timestamp into day and abbreviated month name."""
    return datetime.fromtimestamp(ts).strftime("%d %b")


def counts(store):
    """Calculate record counts and date ranges across all trainee storage tables.

    For each monitored table, counts total rows and calculates the bounding timestamp
    span if timestamp records exist and are non-null. Returns a list of (label, count, span_str) tuples.
    """
    out = []
    with store.conn() as con:
        for table, label, tcol in TABLES:
            n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            span = ""
            if tcol and n:
                lo, hi = con.execute(f"SELECT MIN({tcol}), MAX({tcol}) FROM {table}").fetchone()
                if lo is not None and hi is not None:
                    span = f" ({_fmt(lo)} to {_fmt(hi)})"
            out.append((label, n, span))
    return out


@tool("data_report", SAFE, "Show what data the assistant has stored about the user.", {})
def data_report(s):
    lines = [f"• {label}: {n}{span}" for label, n, span in counts(s.store)]
    try:
        vec = PersonalVectors().count(s.store.key)
        lines.append(f"• Document passages indexed (embeddings): {vec[PersonalVectors.DOCS]}")
        lines.append(f"• Summary embeddings: {vec[PersonalVectors.SUMS]}")
    except Exception:
        pass
    lines.append(f"Activity tracking is {'paused' if recorder_for(s.store).is_paused() else 'on'}; raw activity is "
                 f"deleted after {config.RETENTION_DAYS} days.")
    lines.append("Stored on the assistant server in your private store (visible only to you). The list of your files "
                 "and apps stays on your computer, and so do your notes and tasks (Documents/TraineeAssistant). "
                 "Never stored: screenshots, audio, passwords, private-browsing windows.")
    return {"msg": "\n".join(lines)}


def _wipe_describe(s):
    return "Permanently delete ALL data the assistant has stored about you"


def _wipe_preview(s):
    return "\n".join(f"{label}: {n}" for label, n, _ in counts(s.store) if n)


@tool("wipe_all_data", CONFIRM, "Delete everything the assistant has stored about the user.", {},
      describe=_wipe_describe, preview=_wipe_preview)
def wipe_all_data(s):
    with s.store.conn() as con:
        for table, _, _ in TABLES:
            con.execute(f"DELETE FROM {table}")
        con.execute("DELETE FROM settings")
    try:
        PersonalVectors().delete_user(s.store.key)                # the vectors too
    except Exception:
        pass
    s.store.purge_storage()
    recorder_for(s.store).reset()
    s.ui.push({"type": "tracking", "paused": False, "seconds": None})
    return {"msg": "All data stored on the server has been deleted. Your notes and tasks on this computer were not touched."}


# ---------------- grammar ----------------
@rule(r"what (?:data )?(?:do you|have you) (?:store|stored|collect|collected|keep|have)(?: (?:data )?(?:about|on) me)?"
      r"|show (?:me )?(?:my|the) (?:stored )?data",
      examples=("what data do you store about me",))
def report(m, b):
    b.add("data_report")


@rule(r"(?:wipe|erase|delete|remove|clear)\s+(?:all|everything)(?:\s+of)?(?:\s+(?:my|the))?(?:\s+data)?"
      r"|(?:wipe|erase|delete|remove|clear)\s+(?:all\s+)?(?:my|the)\s+data"
      r"|(?:delete|erase|forget)\s+everything\s+(?:you\s+)?(?:stored|have|know|keep|collected)?\s*(?:about|on)\s+me",
      examples=("wipe all my data", "delete everything you stored about me"))
def wipe(m, b):
    b.add("wipe_all_data")
