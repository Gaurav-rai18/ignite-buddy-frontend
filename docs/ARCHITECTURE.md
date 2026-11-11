# Architecture

## Request flow (server)
`realtime/consumer.py` (auth, framing, limits) → `domain/orchestrator.process(session, text)` → `domain/router.route(text)`:

| Route | How it is decided | Uses LLM? |
|---|---|---|
| command | grammar in `commands/skills/*` (clause splitting, slot filling) | **no** |
| clarify / refuse | rule raised `Incomplete` / `Refuse`, or text starts with open/run/remind/… but nothing matched | no |
| screen / summary / activity / docs | regexes in `domain/router.py` | only to write the answer |
| chat | default | yes, with RAG context when a retriever is enabled |

A command plan is `[{id, tool, args}]`, validated against the tool registry (the allowlist), then run by `commands/executor.py`.
`$1.path` style references pass results between steps. **SERVER tools** (timers, notes, tracking…) run in-process;
**DEVICE tools** (find/open/run…) are sent to the client as `device_call` and answered with `device_result`.

## Where things live
| Data / action | Location |
|---|---|
| model credentials, STT, OCR | server only |
| reminders, timers, activity events, summaries, action log | server (PostgreSQL schema per trainee; SQLite file in dev), `ASSISTANT_DATA/users/<hash>/local.db` (one file per user) |
| **notes, tasks** (`Documents/TraineeAssistant`), file/app name index, folder allowlists, script execution, confirmation dialogs | client only |
| screenshots, audio | in memory only, never stored |

## Add a command (≈10 lines, one file)
```python
# commands/skills/mytools.py   (then add `mytools` to commands/skills/__init__.py, before generic rules)
@tool("set_goal", SAFE, "Save a daily goal.", {"text": "str"})
def set_goal(session, text): ...; return {"msg": "Goal saved."}

@rule(r"my goal is (?P<text>.+)", examples=("my goal is finish module 3",))
def _goal(m, b): b.add("set_goal", text=m.group("text"))
```
`examples` feed the `help` command and a test that asserts every example parses and validates. For a command that must run
on the PC, register `device_tool(...)` in the server and add an `op_<name>` method to `src/client/device/executor.py`
(and the name to `DEVICE_OPS` in `src/shared/protocol.py`).
Rule order = priority (first match wins). Free-text rules are safe in compound sentences because a split is only accepted
if every part parses.

## Knowledge base
`kb/` = `extract` (pdf/pptx/docx/md/txt) -> `chunk` -> `store` (ChromaDB, one collection per space) <- `ingest`/`cli`; `kb/router.py` orders the spaces; `chat/rag/kb.py` is the `Retriever` the chat service uses; `chat/service.py` enforces strict mode (refuse without passages, `NOT_IN_CONTEXT` sentinel). To add a space: add it to `SPACES` (`kb/store.py`) and a `kb.<space>` capability.

## Plugging in RAG
1. Implement `Retriever.retrieve(session, query, k) -> list[Passage]` (`chat/rag/base.py`); `session.user` is available for per-user/batch filtering.
2. Enable it: `RAG_RETRIEVERS="mypkg.kb:KnowledgeBase"` (or `@register("kb")` + `RAG_RETRIEVERS=kb`).
3. Optional: implement `Ingestor` if the corpus accepts uploads. `PersonalDocs` (the `/index` + `/ask` corpus) is a working example.

`ChatService` calls all enabled retrievers, isolates their failures, injects passages into **that request only** (never stored in
history) and the prompt tells the model to cite `[source]`. Nothing else changes. Prompt wording lives in `chat/prompts.py`.

## Protocol
See the docstring of `src/shared/protocol.py` (single source of truth for message names, limits and device ops).

## Scaling notes (known limits, in order of when you will hit them)
* One in-flight request holds one worker thread (`ASSISTANT_WORKER_THREADS`, default 64), including while it waits for a human click. Making the orchestrator async is the next step beyond ~100 concurrent users.
* `realtime/presence.py` and the scheduler are per process. For several server processes set `REDIS_URL` (channel layer), run the scheduler in ONE process, and move presence to Redis.
* Server-side STT processes audio centrally (Vosk, Faster-Whisper, Google SpeechRecognition), freeing trainee machines from running heavyweight speech models.
* Dual database support: SQLite for lightweight dev/offline pilots; swap for PostgreSQL in production with identical model schemas.
* Auth provides JWT tokens validated against Django's user table with full RBAC and TCS Ignite cohort/batch mapping.

## Admin capabilities
Each tool may declare `capability="files.delete"` (see `commands/skills/files.py`). `commands/executor.py` checks
`policy.allows(cap, user_id)` before running the step and explains which switch is off. Add a capability: put it in
`DEFAULT_CAPS` (`domain/policy.py`) and pass `capability=` when registering the tool.

## Frontend and local agent
`frontend/src/state.js` holds ALL message handling as a pure reducer; components only render it.
`src/client/agent/server.py` bridges the page and the central server: UI -> server only for whitelisted types; server -> UI
for everything except `device_call` and `capture_request`, which the agent answers itself (DeviceExecutor / screenshot preview).

## Data flow additions
* **Sync:** Central Django API provides the source of truth; live deltas are pushed through Channels WebSocket groups (`b_<batch>`, `all_trainees`). The agent applies them to local SQLite.
* **Chat memory:** the agent records completed Q&A turns (not commands, not refusals) in local SQLite; `ChatService.hydrate_history` asks for them with the
  `chat_context` device op (last turns + older related turns), and `condense` rewrites follow-ups before retrieval.
* **Mixed sentences:** `commands/parser.parse_mixed` -> router kind `mixed` -> orchestrator runs each half with its own engine.
* **Storage dialects:** Django ORM handles DB abstraction cleanly across SQLite and PostgreSQL.

## Desktop shell
`src/client/desktop/`: launcher auto-detects PySide6 overlay or Electron BrowserWindow. Frameless transparent always-on-top window with click-through masking.
The page asks the shell for things (hit rectangles, hide, quit) through the agent's WebSocket, and the shell asks the page (`activate`/`deactivate`) the same way.
Frontend: `Avatar3D.jsx` (Three.js mascot) · `Bubble.jsx` (voice & text commands) · `AnswerModal.jsx` (markdown answers) · `hit.js` (click-through regions).

## Speech
`src/server/stt/`: `server_transcriber.py` (Vosk, Faster-Whisper, and Google SpeechRecognition engines).
Flow: UI mic captures one-shot audio chunk -> sends to local Agent -> relayed to Central Server STT endpoint (`/api/stt/transcribe/` or direct backend) -> returned text passed to command/chat pipeline. Zero heavy ML dependencies on trainee VDI nodes.
