# Ignite Buddy Admin Console (`frontend-admin`)

The central management interface for the **TCS Ignite Program**, built with **React 18**, **Vite 5**, and **Lucide React**. It communicates with the Ignite Buddy Django backend via secure REST APIs to orchestrate communications, scheduling, Buddy assistant availability, trainee cohorts, and RAG knowledge-base sources.

---

## Features

### 1. Authentication & Security
- **JWT Authentication**: Authenticates with `/api/accounts/login/` returning access and refresh tokens.
- **Session Persistence**: Remembers sessions via `localStorage` (when "Remember me" is checked) or `sessionStorage`.
- **Protected Routing**: Secures `/dashboard`, `/broadcast`, `/schedule`, `/buddy`, `/users`, and `/documents`. Unauthenticated users are redirected to `/login`.
- **RBAC**: Supports Admin, TA, HR, Manager, and Trainee roles.

### 2. Dashboard
- **Campus Metrics**: Live counters for published broadcasts, scheduled timetables, and upcoming events.
- **TCS Ignite Counts**: Live statistics for total trainees, active cohorts (`B49`, `B50`), batches (`A`, `B`), and sub-batches (`A1`, `B1`).
- **Buddy Availability Switch**: Instant control to toggle student AI assistant availability during testing periods.
- **Quick Actions**: One-click shortcuts to post announcements, schedule timetables, or review user rosters.

### 3. Broadcast Announcements
- **Multilevel Scoped Targeting**:
  - **All Users**: Campus-wide broadcast.
  - **By Cohort**: All 300+ trainees in an intake (e.g. `B50`).
  - **By Batch**: Trainees in a specific lecture section (e.g. `B50-A`).
  - **By Sub-Batch**: A single practical lab group (e.g. `B50-A1`).
  - **By Role**: Teaching Assistants, HR, or Managers.
  - **Specific Users**: Multi-select individual trainees.
- **Live Real-Time Toast**: Dispatches immediate WebSocket push alerts to connected trainee desktop assistants.
- **Broadcast History**: Searchable audit log of sent announcements with timestamps and audience metadata.

### 4. Schedule OneDrive Resources
- **Timetable Management**: Publish lecture notes, timetables, and lab instructions via secure OneDrive HTTPS links.
- **Targeted Schedules**: Assign timetable links to specific batches or cohorts.
- **Automated Scheduling**: Set future publication dates and times with live link validation.

### 5. Buddy Availability & Exam Mode Control
- **Campus-Wide Toggle**: Instantly pauses trainee assistants during Project Readiness Assessments (PRA) or internal evaluations.
- **Persistent State**: Persisted in the backend `SystemSetting` table and synchronized across Channels WebSockets.

### 6. Manage Users & Bulk Onboarding
- **Trainee Directory**: Interactive roster displaying Employee ID / Username, Email, Role, Cohort, Batch, Sub-Batch, and last active status.
- **Search & Filters**: Real-time filtering by role, cohort, and batch name.
- **Bulk Excel Import**: Upload `.xlsx` or `.xls` spreadsheets to onboard hundreds of trainees simultaneously. The parser automatically extracts composite batch formats (e.g. `"B50-A1"`) and initializes the hierarchy.

### 7. RAG Knowledge Base (`/documents`)
- **Document Management**: Upload internal policy manuals, Ignite space laboratory guidelines, and assessment criteria (`.pdf` and `.txt`).
- **Automatic Chunking & Ingestion**: Splits documents into chunks and indexes them into the vector store.
- **Vector Deletion Sync**: Removing a document cleanly deletes the physical file and purges its vector embeddings from the index.

---

## Project Structure

```text
frontend-admin/
├── src/
│   ├── app/
│   │   └── App.jsx                 # Route definitions and notification toast container
│   ├── assets/
│   │   └── mascot.png              # Ignite Buddy mascot asset
│   ├── components/
│   │   ├── broadcast/              # Broadcast composer and history list
│   │   ├── buddy/                  # Buddy availability hero and toggle switch
│   │   ├── dashboard/              # Stats grid, quick actions, and recent activity
│   │   ├── documents/              # Document upload modal and document table
│   │   ├── layout/                 # Sidebar, header, navigation, and user avatar menu
│   │   ├── schedule/               # Schedule form and upcoming timetables list
│   │   ├── ui/                     # Accessible input fields, buttons, and dialogs
│   │   └── users/                  # User table, edit modal, and bulk upload modal
│   ├── constants/
│   │   └── index.js                # API base URL (/api) and validation limits
│   ├── hooks/                      # Custom hooks for auth, broadcasts, buddy, etc.
│   ├── pages/                      # Page views for all major console routes
│   ├── services/                   # Axios API client wrappers (apiClient, authService, etc.)
│   └── main.jsx                    # Application entry point
├── package.json
└── vite.config.js                  # Vite configuration with proxy to http://127.0.0.1:8765
```

---

## Development & Build

### Development Mode

**Bash / CMD:**
```bash
npm install
npm run dev
# Starts Vite dev server on http://localhost:5174
# All /api calls are proxied to the backend at http://127.0.0.1:8765
```

### Production Build

**Bash / CMD:**
```bash
npm run build
# Compiles minified bundle into frontend-admin/dist/
```
