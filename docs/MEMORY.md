# Conversation memory — design choice

## Decision: **do not use mem0.ai**

Reasons for this project:

1. **Privacy / policy** — Chat history must stay on the trainee PC (`localdb`).
   mem0 is an external memory service; that conflicts with "local DB only".
2. **Already solved** — `src/client/localdb.py` stores `chat_turns` and the
   server hydrates relevant turns into the session on each chat request
   (`ChatService.hydrate_history`). Follow-ups are condensed for RAG.
3. **Multi-turn UI** — The top-middle conversation panel keeps the current
   thread in React state; both the panel and the bubble can append turns.
   Closing the panel resets the *visible* thread; local DB still has history.

## What we use instead

| Layer | What is stored | Where |
|-------|----------------|-------|
| Current thread | Q&A in the answer panel | React `conversation` state |
| Relevant past turns | Fuzzy-matched prior Q&A | Local SQLite `chat_turns` |
| Server session | Last ~40 messages this connection | In-memory `session.history` |
| Daily summaries | Activity summaries | Server user DB + can be mirrored locally |
| Assignments / timetable | Master on server; **working copy + completion status on PC** | Central DB + local `assignments` / `timetable` |

## Assignments & schedule: local vs central

- **Central DB** remains the admin source of truth (publish / edit / delete).
- **Local DB** already holds a synced copy plus **completion status** (`pending`/`done`).
  That is the right place for trainee-facing "I submitted X" — do not move
  completion into the central DB unless the admin panel needs to grade it.

If the admin later needs completion analytics, add an optional upload of
status from the client; keep the default offline-friendly local copy.
