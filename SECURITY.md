# Security & privacy (v5, central server)

> This replaces the single-machine version. **Read the "Decisions to review" section before a pilot.**

## Trust boundaries
| Boundary | Rule |
|---|---|
| client → server | first-message token auth, per-user identity, size limits, flood guard; server stamps all timestamps |
| server → client | the client does **not** trust the server with its machine: fixed operation set, folder allowlists, symlink-resolved path checks, its own confirmation for scripts, script hash re-checked after approval |
| model | credentials exist only on the server; clients never see them; the model never produces commands (the grammar does) |
| screen / document text | treated as data; that path returns text only and cannot start tools |

## Data inventory
| Data | Where | Retention | Notes |
|---|---|---|---|
| reminders, timers, action log, document chunks | server, per-user SQLite | until the user deletes |
| **notes and tasks** | **trainee's PC only** (`Documents/TraineeAssistant`) | until the user deletes (note delete = `.trash`) | never sent to the server | `wipe all my data` deletes + VACUUM + WAL truncate (`secure_delete=ON`) |
| activity events (app + title) | server | `RETENTION_DAYS` (14) | masked + redacted **on the client first**, again on the server; private windows stored as `(private)`; client stops sending while paused/blocked |
| summaries | server | kept | prose only |
| screen-help history | server | `RETENTION_DAYS` | question + answer only |
| file/app name index | client memory only | process lifetime | never uploaded |
| screenshots, audio | memory only | request lifetime | screenshot needs the user's explicit preview approval |

## Decisions to review (these are changes from v4, which kept everything on the trainee's PC)
1. **Personal data is now on a central server.** Needs: disk encryption, OS-level access control to `ASSISTANT_DATA`, backups policy, no admin API that reads `users/*`. Per-user encryption keys can be added in `Store.db()`. Confirm this with Privacy/Legal before enabling activity tracking for a batch.
2. **Document text** from `/index` folders is uploaded to the server for embedding (redacted first; secrets-type file names skipped). Users should know this.
3. **OCR runs on the server**, so the screenshot (after user approval) is sent to it. Moving OCR to the client would avoid that.

## Implemented
- Fail closed: client locks when disconnected or blocked; server refuses work and scheduler notifications for blocked users.
- Assessment block is server-owned (`core/policy.py`), global or per user; dev switch only when `ASSISTANT_DEBUG=1`.
- No generic `run_command`; blocked intents (delete files, format, install, registry) are refused by the grammar itself.
- `open_url` accepts only http/https (rejects `javascript:`, `file:` etc.).
- Activity: one device at a time feeds a user's timeline; samples are rate-limited per connection.

## File CRUD, native scheduling, admin capabilities
- Admin capabilities (`core/policy.py`) are enforced on the server before any step runs; unknown capability = denied; `files.delete` is off by default.
- The PC independently confines writes to `ASSISTANT_WRITE_ROOTS`, protects roots and the assistant's own folders, refuses executable file types (`.exe .bat .ps1 ...`) for create/rename, never overwrites, and sends deletions to the Recycle Bin after a local confirmation.
- Windows scheduling inputs (`ref`, `kind`, repeat) are validated and the user's text only travels inside a base64 `-EncodedCommand` payload and XML-escaped toast text, so it cannot become PowerShell.
- The "open" tool accepts only names from a fixed allowlist (`device/systemtargets.py`), never a free-form URI or command.
- **Known limitation:** date/time phrases ("tomorrow 5pm") are interpreted in the SERVER's time zone. Run the server in the trainees' time zone (`TZ`) until per-client time zones are added.

## Local agent (React UI) and knowledge base
- The agent listens on 127.0.0.1 only; Host header, WebSocket Origin and a random per-run token are all required, so another web page cannot drive it (DNS rebinding / cross-site WebSocket). The UI can send only a whitelist of message types and can never fabricate device results.
- Scripts and deletions need a visible approval in the UI, and with no UI connected they are refused.
- Knowledge-base answers are grounded: no relevant passage means a fixed refusal without a model call; passage text is treated as data. Knowledge-base spaces can be switched off per account (`kb.ignite`, `kb.general`).
- Documents in the knowledge base are admin-curated; scan them for secrets before `trainee-kb ingest` (only the personal `/index` path applies redaction).

## Databases (v5.1)
- **Local SQLite (PC):** chat history, assignments/timetable copy and an audit log of device operations. The audit log records operation names and non-sensitive arguments only (note text, clipboard text, file content and search words are never written). Pruned by `CHAT_KEEP_DAYS` / `AUDIT_KEEP_DAYS`; "forget our conversation" and "clear my command history" delete on demand. The server never reads this file.
- **PostgreSQL (server):** one schema per trainee; use a dedicated DB role, TLS to the database, and restrict `u_*` schemas to the service account. `wipe all my data` deletes the trainee's rows, vacuums, and removes their vectors from ChromaDB.
- **Admin API:** `X-Admin-Token` (constant-time compare) is the only protection today; the panel page is static and the API is CSRF-exempt because it is token-only. Put it behind the company network/VPN and replace the shared token with SSO before production.
- Corporate proxies: internal Ollama and the agent link bypass `HTTP(S)_PROXY` by default (`trust_env=False`).

## Desktop shell and speech
- The overlay only loads the agent's own page (navigation elsewhere and pop-up windows are refused); the microphone permission is granted to that page only.
- Window click-through uses a mask built from rectangles the page reports; the shell validates and clips them (untrusted input).
- **Speech recognition runs on the trainee's PC through `SpeechRecognition`.** With the default `STT_ENGINE=google` (`recognize_google`) the microphone audio is sent to Google's free web API (unofficial, rate-limited): not acceptable where audio must stay inside the company. Use a local engine (`faster_whisper`, `phonon`, `vosk`) there. The central server never receives audio.
- Global shortcut: `RegisterHotKey` only (no keylogging hook); a shortcut without a modifier is rejected.

## Not done yet (must be done before production)
- [ ] Real authentication (OIDC/JWT validation + device registration) in `transport/auth.py`; today it is a static token table.
- [ ] `wss://` termination, `ASSISTANT_ALLOWED_HOSTS`, origin policy for non-desktop clients.
- [ ] Per-user encryption at rest; audit log of admin access.
- [ ] Gateway-side enforcement of the assessment block (so a modified client gains nothing).
- [ ] Per-user rate limits on LLM calls and `/index` volume.
- [ ] Signed/pinned client builds; secret scanning of indexed documents beyond regex redaction.
