# Ignite Buddy

An enterprise desktop assistant and campus management platform for the **TCS Ignite Program**, combining an AI-powered desktop companion for trainees with a central administration console for staff, teaching assistants, HR, and managers.

```
                           Ignite Buddy Architecture

  ┌────────────────────────────────────────────────────────────────────────────┐
  │                    Admin Console (frontend-admin)                      │
  │        React 18 · Vite · Lucide React · JWT Auth · Tailwind/CSS        │
  │   Dashboard · Buddy Control · Broadcasts · Schedules · RAG · Users     │
  └───────────────────────────────────────┬────────────────────────────────────┘
                                      │ REST API (JSON)
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────────┐
  │                   Ignite Buddy Server (src/server)                     │
  │               Django 5 · Channels 4 · ASGI (Daphne)                    │
  │                                                                        │
  │  REST APIs (DRF)                 Real-time & AI Engine                 │
  │  ├── accounts (RBAC, hierarchy)  ├── WebSocket consumer & presence     │
  │  ├── buddy_controller (exams)    ├── Deterministic command parser      │
  │  ├── notifications (broadcasts)  ├── Policy & RAG knowledge base       │
  │  ├── schedules (timetables)      ├── Server-side STT (Vosk/Whisper/G)  │
  │  ├── documents (vector ingest)   └── Ollama LLM gateway (no client key)│
  │  └── telemetry (chat/activity)                                         │
  │                                                                        │
  │  Database (Dual Support): SQLite (dev) / PostgreSQL (production)       │
  └───────────────────────────────────────▲────────────────────────────────────┘
                                      │ WebSocket (WSS) + HTTP STT
                                      │
  ┌───────────────────────────────────────┴────────────────────────────────────┐
  │                 Trainee Desktop Client (src/client)                    │
  │  Frontend: React 18 · Three.js 3D Avatar · Bubble UI · Lucide React    │
  │  Agent: Local Python executor · One-shot audio recorder (no local STT) │
  │  Shell: Auto-selects Electron or PySide6 overlay window                │
  │  DeviceExecutor: Local file finder · app launcher · script runner      │
  └────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Capabilities

1. **TCS Ignite Program Hierarchy**:
   - **Cohort Level** (e.g. `B49`, `B50`): Top-level intakes of 300–500 trainees.
   - **Major Batch Level** (e.g. `A`, `B`, `C`): Lecture sections and curriculum technology tracks.
   - **Sub-Batch Level** (e.g. `A1` to `A4`, `B1` to `B4`): Practical lab groups of 20–30 trainees seated together.
   - **Physical Labs** (e.g. `Lab 1`, `Lab 2`): Room and machine assignment mapping.
2. **Deterministic Command Execution**:
   - Trainee queries like *"open the react assignment in VS Code"* or *"start a 15-minute timer"* are parsed by code grammar rules. **Zero LLM hallucinations** and instantaneous response times.
3. **Internal Policy & Knowledge Base (RAG)**:
   - Administrators upload internal policy manuals and space rules through the Admin Console. Documents are parsed, chunked, and ingested into a local vector store. The assistant answers trainee questions using verified company context.
4. **Server-Side Speech-to-Text (STT)**:
   - Trainee laptops do not install heavy ML models. Audio is captured in one shot and transcribed on the server via Vosk, Faster-Whisper, or Google SpeechRecognition, fully compatible with corporate Zscaler proxies.
5. **Exam Mode & Instant Buddy Control**:
   - During Project Readiness Assessments (PRA) or exams, instructors can disable Buddy assistants campus-wide, per-cohort, per-batch, or per-lab via the Admin Console or REST APIs.
6. **Corporate Accops VDI Ready**:
   - Engineered for Windows enterprise virtual desktop environments with network proxy awareness and no administrator privilege requirements on trainee nodes.

---

## Project Structure

```text
Ignite_Buddy/
├── frontend/                     # Trainee Assistant UI (React 18 + Vite)
│   ├── src/
│   │   ├── components/           # Avatar3D, Bubble, AnswerModal, Icons
│   │   ├── hooks/                # useAgent, useVoice, useAudioRecorder
│   │   ├── lib/                  # state, vad, speech
│   │   └── App.jsx
│   └── vite.config.js            # Builds directly into src/client/agent/static/
├── frontend-admin/               # Admin Console UI (React 18 + Vite + Lucide)
│   ├── src/
│   │   ├── components/           # Layout, Dashboard, Buddy, Broadcast, Schedule, Users, Docs
│   │   ├── pages/                # Login, Dashboard, BuddyControl, Broadcast, Schedule, Users, Docs
│   │   ├── services/             # apiClient, authService, buddyService, etc.
│   │   └── App.jsx
│   └── vite.config.js            # Dev proxy to Django backend on port 8765
├── desktop-electron/             # Optional Electron overlay container
├── src/
│   ├── shared/                   # Wire protocols, dataclasses, and screen redaction
│   │   ├── protocol.py           # Client-server WebSocket action contracts
│   │   ├── codectx.py            # Code context extraction
│   │   └── redaction.py          # Screen & sensitive text masking
│   ├── server/                   # Central Django + Channels backend
│   │   ├── apps/
│   │   │   ├── accounts/         # User auth, RBAC, Cohort/Batch/SubBatch/Lab models, bulk upload
│   │   │   ├── buddy_controller/ # Exam mode, device status, SystemSetting key-value store
│   │   │   ├── notifications/    # Broadcasts, scoped targeting, recipient inbox tracking
│   │   │   ├── schedules/        # Timetables, OneDrive schedule links
│   │   │   ├── documents/        # KnowledgeDocument model, PDF/TXT chunking, RAG vector store
│   │   │   ├── dashboard/        # Summary analytics and live trainee counts
│   │   │   └── telemetry/        # Central ChatLog and ActivityEvent auditing
│   │   ├── chat/                 # RAG prompt pipelines, contextual policy answering
│   │   ├── commands/             # Deterministic grammar parser & tool executors
│   │   ├── knowledge/            # Chunking, embeddings, and vector store (ChromaDB / SQLite)
│   │   ├── realtime/             # Channels WebSocket consumers & push dispatchers
│   │   ├── stt/                  # Server-side speech-to-text engines
│   │   ├── ignite_server/        # Django settings, ASGI routing, WSGI
│   │   └── run.py                # Server launcher (Daphne CLI runner)
│   └── client/                   # Trainee desktop agent & device executor
│       ├── agent/                # Local aiohttp server & static UI bundle host
│       ├── desktop/              # Launcher (auto: Electron or PySide6 overlay)
│       ├── device/               # DeviceExecutor (files, applications, scripts, vault)
│       └── sensors/              # Window focus and idle state sampler
├── data/                         # Local SQLite databases, media files, knowledge base docs
├── tests/                        # Pytest suite for server, client, STT, and integration
├── manage.py                     # Django management CLI
└── pyproject.toml                # Unified package configuration & CLI entry points
```

---

## Quick Start

### 1. Environment Setup

**Bash (Git Bash):**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -e .
```

**Windows Command Prompt (CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e .
```

### 2. Configure Environment (`.env`)

Create a `.env` file in the project root:

```env
# Server settings
DJANGO_SECRET_KEY=ignite-buddy-dev-secret-key-32chars-min!!
ASSISTANT_HOST=127.0.0.1
ASSISTANT_PORT=8765
ASSISTANT_DEBUG=1

# Database: leave empty for local SQLite (data/ignite_buddy.sqlite3)
# Or set for production PostgreSQL:
# DATABASE_URL=postgresql://postgres:root@localhost:5432/ignite_buddy_db

# LLM Gateway (Organisation Ollama or compatible API)
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=qwen2.5:7b
FAST_MODEL=qwen2.5:3b
EMBED_MODEL=nomic-embed-text

# Server Speech-to-Text engine (google | whisper | vosk)
STT_ENGINE=google
```

### 3. Initialize Database

**Bash / CMD:**
```bash
# Verify system configuration
python manage.py check

# Apply migrations
python manage.py migrate

# Create initial admin account
python manage.py createsuperuser
```

---

## Running the Applications

### 1. Start the Central Backend Server

**Bash / CMD:**
```bash
# Starts Daphne ASGI server listening on port 8765:
ignite-server

# Or using manage.py:
python manage.py runserver 127.0.0.1:8765
```

### 2. Run the Admin Console (`frontend-admin`)

**Bash / CMD:**
```bash
# In a separate terminal:
cd frontend-admin
npm install
npm run dev
# Opens at http://localhost:5174 (proxies /api requests to :8765)
```

To build production assets:
```bash
cd frontend-admin
npm run build
```

### 3. Run the Trainee Assistant UI (`frontend`)

**Bash / CMD:**
```bash
# Build the React trainee bundle into the Python client:
cd frontend
npm install
npm run build
cd ..

# Start the trainee agent (headless browser mode for development):
ignite-client

# Or start the native desktop overlay (PySide6 or Electron):
ignite-desktop
```

---

## API Summary

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/health` | `GET` | Health check probe |
| `/auth/login` | `POST` | Trainee desktop authentication (returns JWT & cohort/batch mapping) |
| `/api/accounts/login/` | `POST` | Admin console login (issues JWT access & refresh tokens) |
| `/api/accounts/users/` | `GET/POST` | List and create campus users |
| `/api/accounts/users/bulk-upload/` | `POST` | Bulk onboard trainees from Excel spreadsheets |
| `/api/accounts/cohorts/` | `GET` | List TCS Ignite cohorts (`B49`, `B50`, etc.) |
| `/api/accounts/batches/` | `GET` | List major sections (`A`, `B`, `C`) |
| `/api/accounts/sub-batches/` | `GET` | List lab groups (`A1`, `A2`, `B1`, etc.) |
| `/api/accounts/labs/` | `GET` | List physical computer training labs |
| `/api/settings/buddy/` | `GET/PATCH` | Global Buddy availability toggle & exam-mode lock |
| `/api/notifications/broadcast/` | `POST` | Create announcement scoped to Cohort, Batch, Sub-Batch, Role, or All |
| `/api/notifications/broadcast/history/` | `GET` | View historical announcements |
| `/api/schedules/` | `GET/POST` | View and schedule OneDrive timetable resources |
| `/api/documents/` | `GET/POST` | Upload and list RAG knowledge documents (PDF/TXT) |
| `/api/documents/<id>/` | `DELETE` | Delete knowledge document and purge its vectors from ChromaDB |
| `/api/dashboard/` | `GET` | Real-time campus metrics and trainee counts |

---

## Testing

Run the test suite using `pytest`:

**Bash / CMD:**
```bash
pytest
```

Included test suites:
- `tests/server/test_parser.py`: Deterministic grammar parser verification.
- `tests/server/test_server_stt.py`: Audio transcription and proxy connectivity tests.
- `tests/server/test_rag_and_chat.py`: Retrieval and prompt composition tests.
- `tests/client/test_executor.py`: Safe device action execution tests.
