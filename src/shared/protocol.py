"""Wire contract shared by the server and every client. Import this on both sides; never duplicate the strings.

CLIENT -> SERVER                                   SERVER -> CLIENT
 {type:"auth", token, device_id, version}           {type:"hello_ok", user, debug, models, tracking:{paused,seconds}}
 {type:"settings", tts:bool}                        {type:"policy", blocked, reason}
 {type:"text", text}                                {type:"state", state: idle|listening|thinking|generating|speaking}
 {type:"audio", data}  (one-shot audio sent to server)  {type:"transcript", text, final}   (server -> client)
 {type:"cancel"}   (also = barge-in)                {type:"say", text}                (tool/status lines)
 {type:"confirm_response", id, approved}            {type:"token", text} / {type:"message_end"}   (streamed LLM output)
 {type:"choose_response", id, choice|null}          {type:"confirm_request", id, title, preview}
 {type:"capture_response", id, image_b64|null,...}  {type:"choose_request", id, question, options}
 {type:"device_result", id, status, ...}            {type:"capture_request", id}      (screen help)
 {type:"activity_sample", app, title, idle}         {type:"device_call", id, op, args}   (run something ON the client)
 {type:"playback_done"} {type:"ping"}               {type:"tracking", paused, seconds}   (pause/resume tracking)
 {type:"dev_set_blocked", blocked}  (DEBUG only)    {type:"speak", text} {type:"pong"} {type:"blocked", reason}
 {type:"sync_cursor" in auth}                       {type:"notification", kind: reminder|timer|summary, text}
                                                    {type:"error", message}

The first client message MUST be `auth`; everything else is ignored until it succeeds (close code 4401 on failure).
The server never touches the client's disk, apps or screen directly: it sends `device_call` and the client decides
(allowlisted folders, its own confirmation dialog) and answers with `device_result`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PROTOCOL_VERSION = 3
REFUSAL_PREFIX = "I'm sorry, I can't answer that."      # every "not in my knowledge base" reply starts with this

# ---- limits (enforced by the receiver, never trusted from the sender) ----
MAX_TEXT = 2000
MAX_AUDIO_BYTES = 16000 * 2 * 60          # 60 s of PCM16 mono 16 kHz
MAX_SCREENSHOT_BYTES = 8_000_000
MAX_APP_LEN, MAX_TITLE_LEN = 100, 300
CLOSE_UNAUTHORIZED = 4401

# ---- device operations (server -> client) ----
FIND_FOLDER, FIND_FILE = "find_folder", "find_file"
OPEN_APP, OPEN_IN_APP, OPEN_FOLDER, OPEN_FILE = "open_app", "open_in_app", "open_folder", "open_file"
OPEN_TARGET, OPEN_URL, WEB_SEARCH, RUN_FILE = "open_target", "open_url", "web_search", "run_file"
READ_OPEN_FILE, LIST_DOCUMENTS, READ_DOCUMENT, REFRESH_INDEX = (
    "read_open_file", "list_documents", "read_document", "refresh_index")
# files (CRUD) - capability-gated by the admin policy on the server, path-checked again on the client
CREATE_FOLDER, CREATE_FILE, RENAME_PATH, MOVE_PATH, COPY_PATH, DELETE_PATH, READ_FILE, LIST_FOLDER = (
    "create_folder", "create_file", "rename_path", "move_path", "copy_path", "delete_path", "read_file", "list_folder")
# notes + tasks live as files in a dedicated folder on the trainee's PC
ADD_NOTE, LIST_NOTES, SEARCH_NOTES, READ_NOTE, APPEND_NOTE, UPDATE_NOTE, DELETE_NOTE, OPEN_NOTES = (
    "add_note", "list_notes", "search_notes", "read_note", "append_note", "update_note", "delete_note", "open_notes_folder")
ADD_TASK, LIST_TASKS, COMPLETE_TASK, DELETE_TASK = "add_task", "list_tasks", "complete_task", "delete_task"
# trainee data kept in the LOCAL SQLite database on the PC (chat history, assignments, timetable, audit log)
CHAT_CONTEXT, LIST_ASSIGNMENTS, SET_ASSIGNMENT, NEXT_ASSIGNMENT = "chat_context", "list_assignments", "set_assignment", "next_assignment"
SHOW_TIMETABLE, NEXT_CLASS, SHOW_AUDIT, CLEAR_AUDIT, CLEAR_CHAT = "show_timetable", "next_class", "show_audit", "clear_audit", "clear_chat_history"
# the OS itself
NATIVE_SCHEDULE, NATIVE_CANCEL = "native_schedule", "native_cancel"      # Windows Task Scheduler + toast
OPEN_SYSTEM, LOCK_SCREEN, CLIPBOARD_SET, GET_TIME = "open_system", "lock_screen", "clipboard_set", "get_time"
DEVICE_OPS = frozenset({FIND_FOLDER, FIND_FILE, OPEN_APP, OPEN_IN_APP, OPEN_FOLDER, OPEN_FILE, OPEN_TARGET,
                        OPEN_URL, WEB_SEARCH, RUN_FILE, READ_OPEN_FILE, LIST_DOCUMENTS, READ_DOCUMENT, REFRESH_INDEX,
                        CREATE_FOLDER, CREATE_FILE, RENAME_PATH, MOVE_PATH, COPY_PATH, DELETE_PATH, READ_FILE,
                        LIST_FOLDER, ADD_NOTE, LIST_NOTES, SEARCH_NOTES, READ_NOTE, APPEND_NOTE, UPDATE_NOTE,
                        DELETE_NOTE, OPEN_NOTES, ADD_TASK, LIST_TASKS, COMPLETE_TASK, DELETE_TASK,
                        NATIVE_SCHEDULE, NATIVE_CANCEL, OPEN_SYSTEM, LOCK_SCREEN, CLIPBOARD_SET, GET_TIME,
                        CHAT_CONTEXT, LIST_ASSIGNMENTS, SET_ASSIGNMENT, NEXT_ASSIGNMENT, SHOW_TIMETABLE, NEXT_CLASS,
                        SHOW_AUDIT, CLEAR_AUDIT, CLEAR_CHAT})

OK, ERROR, AMBIGUOUS, CANCELLED = "ok", "error", "ambiguous", "cancelled"
STATUSES = frozenset({OK, ERROR, AMBIGUOUS, CANCELLED})


@dataclass
class DeviceResult:
    """Outcome of one device operation."""
    status: str
    data: dict = field(default_factory=dict)      # on ok: {"msg": str, "path"?: str, ...}
    message: str = ""                              # on error
    question: str = ""                             # on ambiguous
    options: list = field(default_factory=list)    # on ambiguous

    @classmethod
    def ok(cls, **data): return cls(OK, data)
    @classmethod
    def error(cls, message): return cls(ERROR, message=str(message))
    @classmethod
    def ambiguous(cls, question, options): return cls(AMBIGUOUS, question=question, options=list(options))
    @classmethod
    def cancelled(cls): return cls(CANCELLED)

    def to_wire(self) -> dict:
        return {"status": self.status, "data": self.data, "message": self.message,
                "question": self.question, "options": self.options}

    @classmethod
    def from_wire(cls, msg) -> "DeviceResult":
        """Defensive parse of an untrusted client message."""
        if not isinstance(msg, dict) or msg.get("status") not in STATUSES:
            return cls.error("Malformed device result")
        data, opts = msg.get("data"), msg.get("options")
        return cls(msg["status"], data if isinstance(data, dict) else {},
                   str(msg.get("message") or "")[:2000], str(msg.get("question") or "")[:500],
                   [str(o)[:500] for o in opts][:20] if isinstance(opts, list) else [])
