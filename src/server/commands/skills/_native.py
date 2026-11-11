"""Mirror a server-side reminder/timer into the trainee's Windows (Task Scheduler + alarm toast). Best effort:
if the PC is not Windows, the admin disabled `native.schedule`, or the call fails, the server scheduler notifies instead."""
import hashlib

from server.domain import policy
from server.domain.session import Cancelled
from server.features import personal
from shared import protocol as P


def ref(session, kind: str, row_id: int) -> str:
    """Unique per assistant user, so two accounts on one PC never collide."""
    return f"{hashlib.sha256(session.user.id.encode()).hexdigest()[:8]}-{kind}{row_id}"


def mirror(session, table: str, kind: str, row_id: int, at_ts: float, text: str, repeat: str = "") -> bool:
    if not policy.allows("native.schedule", session.user.id):
        return False
    try:
        res = session.ui.device_call(P.NATIVE_SCHEDULE, {"ref": ref(session, kind, row_id), "kind": kind,
                                                         "at": str(int(at_ts)), "text": text[:200], "repeat": repeat})
    except Cancelled:
        raise
    except Exception:
        return False
    if res.status == P.OK:
        personal.mark_native(session.store, table, row_id)
        return True
    return False


def unmirror(session, table: str, kind: str, row_id: int):
    if personal.is_native(session.store, table, row_id):
        try:
            session.ui.device_call(P.NATIVE_CANCEL, {"ref": ref(session, kind, row_id)})
        except Cancelled:
            raise
        except Exception:
            pass
