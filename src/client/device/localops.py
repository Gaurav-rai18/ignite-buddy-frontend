"""Device operations backed by the local SQLite database: assignments, timetable, audit log, chat context."""
import time
from datetime import datetime, timedelta

from rapidfuzz import fuzz

from client.localdb import LocalDB
from .errors import Ambiguity, Declined, DeviceError


def _norm_hm(s: str) -> str:
    """Zero-pad HH:MM so lexical compare and sort match clock order (9:30 < 10:00)."""
    try:
        h, m = str(s).strip().split(":", 1)
        return f"{int(h):02d}:{int(m):02d}"
    except (TypeError, ValueError):
        return str(s or "")


DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _fmt_due(ts) -> str:
    if ts is None:
        return "no due date"
    d = datetime.fromtimestamp(ts)
    left = (d - datetime.now()).total_seconds()
    when = d.strftime("%a %d %b, %I:%M %p")
    if left < 0:
        return f"{when} (overdue)"
    return f"{when} (in {int(left // 86400)}d {int(left % 86400 // 3600)}h)" if left >= 86400 else f"{when} (in {int(left // 3600)}h)"


class LocalOps:
    def __init__(self, db: LocalDB, confirm):
        self.db, self.confirm = db, confirm

    def ops(self):
        return {n[3:]: getattr(self, n) for n in dir(self) if n.startswith("op_")}

    # ---------------- chat ----------------
    def op_chat_context(self, a):
        return {"turns": self.db.chat_context(a.get("query", ""))}

    def op_clear_chat_history(self, a):
        if not self.confirm("Forget our conversation history?", "Only the history kept on this computer is deleted."):
            raise Declined
        return {"msg": f"Deleted {self.db.clear_chat()} remembered conversation turns."}

    # ---------------- assignments ----------------
    def op_list_assignments(self, a):
        flt = (a.get("filter") or "pending").lower()
        rows = self.db.assignments()
        if flt == "pending":
            rows = [r for r in rows if r[4] != "done"]
        elif flt == "done":
            rows = [r for r in rows if r[4] == "done"]
        elif flt == "week":
            end = (datetime.now() + timedelta(days=7)).timestamp()
            rows = [r for r in rows if r[4] != "done" and r[3] is not None and r[3] <= end]
        if not rows:
            return {"msg": "No assignments." if flt == "all" else f"No {flt} assignments."}
        return {"msg": "\n".join(f"{'[DONE]' if st == 'done' else '[ ]'} {t}: {_fmt_due(due)}" for _, t, _, due, st in rows)}

    def op_next_assignment(self, a):
        rows = [r for r in self.db.assignments() if r[4] != "done" and r[3] is not None]
        if not rows:
            return {"msg": "You have no pending assignments with a due date."}
        _, t, desc, due, _ = rows[0]
        return {"msg": f"Next: {t}, due {_fmt_due(due)}." + (f"\n{desc}" if desc else "")}

    def op_set_assignment(self, a):
        status = a["status"]
        if status not in ("pending", "done"):
            raise DeviceError("Status must be done or pending.")
        rows = self.db.assignments()
        if a.get("choice"):
            hit = [r for r in rows if r[1] == a["choice"]]
        else:
            q = a["query"].lower().strip()
            scored = sorted(((fuzz.WRatio(q, r[1].lower()), r) for r in rows), key=lambda x: -x[0])
            if not scored or scored[0][0] < 60:
                raise DeviceError(f"No assignment matches '{a['query']}'.")
            close = [r for s, r in scored if s >= scored[0][0] - 5]
            if len(close) > 1:
                raise Ambiguity("Which assignment?", [r[1] for r in close[:5]])
            hit = [close[0]]
        if not hit:
            raise DeviceError("That assignment no longer exists.")
        self.db.set_assignment_status(hit[0][0], status)
        return {"msg": f"Marked '{hit[0][1]}' as {status}."}

    # ---------------- timetable ----------------
    @staticmethod
    def _slots_text(rows) -> str:
        lines = []
        for _, s, e, t, loc in rows:
            tag = " **[TEST BLACKOUT]**" if "[TEST]" in t or "test" in t.lower() or "exit" in t.lower() else ""
            clean_title = t.replace("[TEST]", "").strip()
            loc_str = f" in **{loc}**" if loc else ""
            lines.append(f"• **{s} - {e}**: {clean_title}{loc_str}{tag}")
        return "\n".join(lines)

    def op_show_timetable(self, a):
        day = (a.get("day") or "today").lower().strip()
        today = datetime.now().weekday()
        home_lab = self.db.get_meta("home_lab")
        sub_batch = self.db.get_meta("sub_batch")
        ta = self.db.get_meta("primary_ta")
        anchor = f"*(Sub-batch: **{sub_batch}** · Home Lab: **{home_lab}**" + (f" · TA: **{ta}**" if ta else "") + ")*\n\n" if home_lab else ""

        if day in ("week", "this week", "weekly", "all"):
            rows = self.db.slots()
            if not rows:
                if home_lab:
                    return {"msg": f"Your timetable is not loaded yet.\nYour assigned workspace is **Home Lab: {home_lab}** (Sub-batch {sub_batch})."}
                return {"msg": "Your timetable is empty (no schedule has been published yet)."}
            out = ["### Weekly Timetable\n" + anchor]
            for wd in range(5):  # 5 working days (Monday - Friday)
                day_rows = sorted([r for r in rows if r[0] == wd], key=lambda r: _norm_hm(r[1]))
                if day_rows:
                    out.append(f"\n**{DAYS[wd].capitalize()}**:\n" + self._slots_text(day_rows))
            return {"msg": "\n".join(out)}
        wd = {"today": today, "tomorrow": (today + 1) % 7, "yesterday": (today - 1) % 7}.get(day)
        if wd is None:
            wd = next((i for i, d in enumerate(DAYS) if d.startswith(day[:3])), None)
        if wd is None:
            raise DeviceError(f"I don't know the day '{day}'.")
        rows = self.db.slots(wd)
        if not rows:
            if home_lab:
                return {"msg": f"Nothing scheduled for {DAYS[wd].capitalize()}.\nPlease report to your **Home Lab: {home_lab}** (Sub-batch {sub_batch})."}
            return {"msg": f"Nothing scheduled for {DAYS[wd].capitalize()}."}
        return {"msg": f"### Timetable for {DAYS[wd].capitalize()}\n{anchor}" + self._slots_text(rows)}

    def op_next_class(self, a):
        now = datetime.now()
        cur_hm = now.strftime("%H:%M")
        today_wd = now.weekday()
        home_lab = self.db.get_meta("home_lab")
        sub_batch = self.db.get_meta("sub_batch")
        ta = self.db.get_meta("primary_ta")
        seat_ctx = (
            f"Outside scheduled lecture hours, please be in your **Home Lab: {home_lab}**"
            + (f" (Sub-batch {sub_batch})" if sub_batch else "")
            + (f" with TA {ta}." if ta else ".")
        ) if home_lab else ""

        # Check if a class/lecture is currently in session right now
        for _, s, e, t, loc in self.db.slots(today_wd):
            if _norm_hm(s) <= cur_hm < _norm_hm(e):
                loc_str = f" in **{loc}**" if loc else ""
                clean_title = t.replace("[TEST]", "").strip()
                test_warn = " *(Assessment in progress - Buddy is in test lockdown)*" if "[TEST]" in t or "test" in t.lower() else ""
                return {"msg": f"Currently in session ({s} - {e}): **{clean_title}**{loc_str}.{test_warn}"}

        for offset in range(8):
            wd = (now.weekday() + offset) % 7
            for _, s, e, t, loc in self.db.slots(wd):
                if offset or _norm_hm(s) > cur_hm:
                    day = "today" if offset == 0 else "tomorrow" if offset == 1 else DAYS[wd].capitalize()
                    loc_str = f" in **{loc}**" if loc else ""
                    clean_title = t.replace("[TEST]", "").strip()
                    test_note = " *(Assessment / Test)*" if "[TEST]" in t or "test" in t.lower() else ""
                    prefix = f"{seat_ctx}\n\n" if seat_ctx else ""
                    return {"msg": f"{prefix}Your next lecture is **{clean_title}** {day} at **{s} - {e}**{loc_str}.{test_note}"}

        if home_lab:
            return {"msg": f"No upcoming lectures found. Your designated seating is **Home Lab: {home_lab}**" + (f" for sub-batch {sub_batch}" if sub_batch else "") + (f" (Primary TA: {ta})" if ta else "") + "."}
        return {"msg": "Nothing is scheduled in your timetable right now."}

    # ---------------- audit ----------------
    def op_show_audit(self, a):
        rows = self.db.recent_audit(15)
        if not rows:
            return {"msg": "No commands have been recorded yet."}
        return {"msg": "\n".join(f"• {time.strftime('%d %b %H:%M', time.localtime(ts))}  {op} {args}  [{st}]" for ts, op, args, st in rows)}

    def op_clear_audit(self, a):
        if not self.confirm("Clear the record of commands run on this computer?", ""):
            raise Declined
        return {"msg": f"Deleted {self.db.clear_audit()} audit entries."}
