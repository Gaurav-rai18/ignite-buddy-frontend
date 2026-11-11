"""
Plan executor: runs a validated plan step by step.
 - resolves "$1.path" references from earlier results
 - SERVER tools run here; DEVICE tools are sent to the client (which enforces its own allowlist + confirmation)
 - asks the user to confirm risky server-side steps and to choose when a match is ambiguous
 - stops on the first failure; logs every action to the user's store
Plans must come ONLY from the trainee's own message, never from screen/OCR/document text (prompt-injection guard).
"""
import json
import time

from server.domain import policy
from shared import protocol as P
from .model import BLOCKED, CONFIRM, DEVICE, Ambiguous, ToolError
from .registry import REGISTRY
from .validate import REF


def _log(store, tool, args, status, detail=""):
    with store.conn() as con:
        con.execute("INSERT INTO actions(ts,tool,args,status,detail) VALUES (?,?,?,?,?)",
                    (time.time(), tool, json.dumps(args), status, (detail or "")[:500]))


def resolve_args(args: dict, results: dict) -> dict:
    out = {}
    for k, v in args.items():
        m = REF.match(v)
        if m:
            res = results.get(int(m.group(1)), {})
            if m.group(2) not in res:
                raise ToolError(f"Step {m.group(1)} produced no '{m.group(2)}'")
            v = res[m.group(2)]
        out[k] = v
    return out


class _Cancelled(Exception):
    pass


def _run_device(session, t, args) -> dict:
    ui = session.ui
    res = ui.device_call(t.name, args)
    if res.status == P.AMBIGUOUS:
        choice = ui.choose(res.question or "Which one did you mean?", res.options)
        if not choice:
            raise _Cancelled
        res = ui.device_call(t.name, {**args, "choice": choice})
    if res.status == P.CANCELLED:
        raise _Cancelled
    if res.status != P.OK:
        raise ToolError(res.message or f"{t.name} failed on your computer")
    return res.data


def run_plan(session, steps: list[dict]) -> bool:
    ui, store = session.ui, session.store
    results: dict[int, dict] = {}
    for step in steps:
        t = REGISTRY[step["tool"]]
        try:
            args = resolve_args(step["args"], results)
            if t.level == BLOCKED:
                raise ToolError("This action is blocked by policy")
            if t.capability and not policy.allows(t.capability, session.user.id):
                raise ToolError(f"Your administrator has not enabled this for your account ({t.capability}).")
            if t.where == DEVICE:
                out = _run_device(session, t, args)                  # a CONFIRM device tool asks on the client itself
            else:
                if t.level == CONFIRM:
                    title = t.describe(session, **args) if t.describe else f"Run {t.name}"
                    preview = t.preview(session, **args) if t.preview else ""
                    if not ui.confirm(title, preview):
                        _log(store, t.name, args, "cancelled")
                        ui.say("Cancelled. Remaining steps skipped.")
                        return False
                try:
                    out = t.fn(session, **args)
                except Ambiguous as a:
                    choice = ui.choose(a.question, a.options)
                    if not choice:
                        raise _Cancelled
                    out = a.finish(choice) if a.finish else {"path": choice, "msg": f"Using {choice}"}
            results[step["id"]] = out
            if isinstance(out, dict) and "items" in out and "folder" in out:
                ui.push({"type": "folder_listing", "folder": out.get("folder", ""), "path": out.get("path", ""), "items": out.get("items", [])})
            msg = out.get("msg", "done")
            _log(store, t.name, args, "ok", msg)
            if len(steps) > 1:
                ui.say(f"Step {step['id']}: {msg}")
            else:
                ui.say(msg)
        except _Cancelled:
            _log(store, t.name, step["args"], "cancelled")
            ui.say("Cancelled. Remaining steps skipped.")
            return False
        except ToolError as e:
            _log(store, t.name, step["args"], "error", str(e))
            if len(steps) > 1:
                ui.say(f"Step {step['id']} Failed: {e}. Stopping.")
            else:
                ui.say(f"Failed: {e}")
            return False
    return True
