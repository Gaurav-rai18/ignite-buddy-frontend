# Ignite Buddy Codebase Map

## Mental Model

```
  Trainee PC (Thin Client)                    Central Server (Django + Channels)
  ─────────────────────────                   ──────────────────────────────────
  React UI  ←→  local Agent  ←──wss──→  realtime (Channels ASGI)
  desktop shell   │                      │
  DeviceExecutor  │                      ├─ apps/ (REST APIs for Admin & RAG)
  sensors         │                      │    ├─ accounts (RBAC, Cohort/Batch/SubBatch)
  (one-shot mic)  │                      │    ├─ buddy_controller (Exam locks)
                  │                      │    ├─ notifications (Broadcasts)
                  │                      │    ├─ schedules (Timetables)
                  │                      │    ├─ documents (RAG file ingest)
                  │                      │    └─ telemetry (Chat/activity logs)
                  │                      ├─ stt/ (Server-side speech recognition)
                  │                      ├─ domain/ (Route + orchestrate)
                  │                      ├─ commands/ (Deterministic tools)
                  │                      └─ chat/ + knowledge/ (RAG + Ollama LLM)
```

## `src/` Layout

```text
src/
├── shared/                       # Protocol definitions and screen redaction
│   ├── protocol.py               # WebSocket action contracts (device_call, token, etc.)
│   ├── codectx.py                # Source code context extractor
│   └── redaction.py              # Sensitive token and screen masking
├── server/                       # Central Django + Channels backend
│   ├── apps/
│   │   ├── accounts/             # Cohort, Batch, SubBatch, Lab, User models & bulk Excel import
│   │   ├── buddy_controller/     # Exam mode controls, SystemSetting persistent store
│   │   ├── notifications/        # Scoped broadcasts & recipient delivery tracking
│   │   ├── schedules/            # Timetable links & OneDrive schedules
│   │   ├── documents/            # RAG knowledge documents, PDF parsing, vector sync
│   │   ├── dashboard/            # Real-time metrics summary API
│   │   └── telemetry/            # Central ChatLog and ActivityEvent auditing
│   ├── chat/                     # RAG prompt templates & conversation service
│   ├── commands/                 # Deterministic grammar parser & skill handlers
│   ├── ignite_server/            # Django settings.py, urls.py, asgi.py, wsgi.py
│   ├── knowledge/                # Chunking, embeddings, and vector store (ChromaDB / SQLite)
│   ├── llm/                      # Ollama client and model gateway
│   ├── realtime/                 # Channels WebSocket consumer & presence manager
│   ├── stt/                      # Vosk, Faster-Whisper, and Google SpeechRecognition
│   ├── channels_push.py          # Safe async group dispatch helper
│   ├── config.py                 # Server configuration and environment loading
│   └── run.py                    # Daphne ASGI server CLI entry point
└── client/                       # Trainee desktop agent & device executor
    ├── agent/                    # Local aiohttp server & static UI bundle host
    ├── desktop/                  # Shell launcher (auto-selects Electron or PySide6)
    ├── device/                   # Safe DeviceExecutor (file finder, app launcher, scripts)
    ├── sensors/                  # Window focus and idle state sampler
    ├── localdb.py                # Local offline client cache
    └── config.py                 # Client configuration and environment loading
```

## Frontends

| Directory | Stack | Purpose |
|-----------|-------|---------|
| `frontend/` | React 18, Vite 5, Three.js, Lucide | Trainee Assistant desktop overlay UI |
| `frontend-admin/` | React 18, Vite 5, Axios, Lucide | Admin Console UI (Dashboard, Users, Buddy Control, RAG) |

## Entry Points

| Command | Target Module | Description |
|---------|---------------|-------------|
| `ignite-server` | `server.run:main` | Central Daphne ASGI server on port 8765 |
| `ignite-client` | `client.agent.server:main` | Headless trainee agent for browser testing |
| `ignite-desktop` | `client.desktop.launcher:main` | Native desktop overlay (Electron or PySide6) |
| `manage.py` | `manage:main` | Django administrative CLI (migrate, createsuperuser, etc.) |
