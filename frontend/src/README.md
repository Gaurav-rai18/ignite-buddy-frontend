# Desktop overlay UI (React)

Served by the local agent on 127.0.0.1 and shown either inside the PySide6
shell (`trainee-desktop`) or in a normal browser (`trainee-agent`).

| Folder | Contents |
|--------|----------|
| `components/` | Presentational pieces: Avatar, Bubble, AnswerModal |
| `hooks/` | `useAgent` (WS to local agent), `useVoice` (mic + VAD) |
| `lib/` | Pure logic: reducer state, VAD, hit-rect collection |

Build: from repo root run `make build-ui` (writes into
`src/assistant_client/agent/static/`). Tests: `npm test` in this folder.
