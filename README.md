# Ignite Buddy Admin Console

An enterprise campus administration console built with **React (Vite)**, **Django REST Framework**, and **SQLite**. Designed for managing campus-wide communications, scheduling study resources, orchestrating Buddy AI availability, administering user roles, and curating RAG knowledge-base documents.

---

## Key Features

### 1. Authentication & Route Protection
- **Login Page**: Two-column layout with Ignite Buddy 3D mascot, feature highlights, and a floating authentication card matching the enterprise console theme.
- **Demo Credentials**: Pre-filled for quick evaluation:
  - **Email**: `admin@campus.demo`
  - **Password**: `admin123` *(any valid email and 4+ character password)*
- **Security & Session**: Remembers user sessions via `localStorage` (when "Remember me" is selected) or `sessionStorage`, password show/hide visibility toggle, and client-side validation.
- **Protected Routes**: Restricts console routes (`/dashboard`, `/broadcast`, `/schedule`, `/buddy`, `/users`, `/documents`) to authenticated users, automatically redirecting unauthenticated requests to `/login`.
- **Sign Out**: Accessible from the administrator avatar menu in both the topbar and sidebar.

### 2. Dashboard
- **Real-Time Campus Overview**: Live count of published announcements, scheduled OneDrive links, and immediate upcoming publish counts.
- **Buddy AI Availability**: Global toggle to enable or disable Buddy exam-mode assistance across campus.
- **At-A-Glance Activity**: Recent broadcast activity stream and quick actions.
- **Resilient Error Handling**: Sanitizes backend responses and presents clean, human-readable notifications.

### 3. Broadcast Announcements
- Create and dispatch announcements to specific campus audiences (*All students, First year, Second year, Third year, Final year*).
- Live preview with countdown limits (160 characters for titles, 2,000 for messages).
- Historical announcement log with creation timestamps and recipient metadata.

### 4. Schedule OneDrive Resources
- Schedule study materials, syllabi, and lecture slides via secure OneDrive HTTPS links.
- Set future publish date and time with client and server-side URL validation.
- Organized upcoming schedule view with direct links and publication statuses.

### 5. Buddy Control
- Exam-mode enforcement switch to toggle student AI assistant availability during testing periods.
- Live backend persistence through the Django settings API.

### 6. Manage Users (`/users`)
- **Campus User Administration**: Interactive table displaying user avatars, roles (*Admin*, *Student*), departments, and active/inactive statuses.
- **Search & Filters**: Real-time filtering across name, email, department, and role.
- **Add / Edit User**: Accessible modal with field validation and immediate state update.
- **Delete Confirmation**: Safe deletion workflow with modal confirmation dialog.

### 7. Add Documents — RAG Knowledge Base (`/documents`)
- **Knowledge Retrieval Management**: Upload reference documents to feed Ignite Buddy's retrieval-augmented generation (RAG) pipeline.
- **Supported File Types**: `.pdf` and `.txt` (up to 10 MB per file) with client-side MIME and extension validation.
- **Document Lifecycle**: Tracks processing statuses (`Uploaded` → `Processing` → `Ready for RAG` / `Failed`).
- **Inspection & Search**: Search by filename/type, filter by lifecycle status, and view document details (chunk count, indexing status, upload timestamp).
- **Safe Removal**: Deletion confirmation dialog to remove knowledge sources from the retrieval index.

---

## Project Structure

```text
campus-admin-panel/
├── backend/
│   ├── config/
│   │   ├── settings.py         # Django settings, CORS, and DRF config
│   │   └── urls.py             # Root URL routing (/api/ endpoint)
│   ├── core/
│   │   ├── models.py           # Broadcast, ScheduledLink, SiteSetting models
│   │   ├── serializers.py      # DRF model serializers
│   │   ├── urls.py             # API route registration
│   │   └── views.py            # ViewSets and custom API views
│   ├── db.sqlite3              # SQLite database
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── App.jsx         # Routes, AuthProvider, protected layouts
│   │   ├── assets/
│   │   │   └── mascot.png      # Transparent Ignite Buddy mascot asset
│   │   ├── components/
│   │   │   ├── dashboard/      # HeroBanner, StatsGrid, RecentActivity, QuickActions
│   │   │   ├── documents/      # DocumentUpload, DocumentList, Details, DeleteDialog
│   │   │   ├── layout/         # AppLayout, Topbar, Sidebar, ProtectedRoute, Footer
│   │   │   ├── ui/             # ErrorBanner, Toast, Modal, Dropdown
│   │   │   └── users/          # UserTable, UserFormModal, DeleteUserDialog
│   │   ├── constants/          # API URLs, limits, options
│   │   ├── hooks/              # useAuth, useDashboard, useUsers, useDocuments, etc.
│   │   ├── pages/              # Login, Dashboard, Broadcast, Schedule, BuddyControl, ManageUsers, AddDocuments
│   │   ├── services/           # apiClient, authService, usersService, documentsService, etc.
│   │   ├── test/               # Vitest unit and integration test suites
│   │   ├── utils/              # error.js, validation.js, date.js
│   │   └── styles.css          # Design system tokens and component styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**

---

### Step 1: Start the Django Backend

Open a PowerShell or command terminal:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

The Django REST API runs at: `http://127.0.0.1:8000/api/`

---

### Step 2: Start the React Frontend

Open a second terminal window:

```powershell
cd frontend
npm install
npm run dev
```

Open the local development URL printed by Vite (typically `http://localhost:5173` or `http://localhost:5174`).

---

## Testing & Quality Assurance

### Run Unit Tests
```powershell
cd frontend
npm test
```
Or run directly with the threads pool:
```powershell
npx vitest run src/test/authAndError.test.js --pool=threads
```

### Production Build
```powershell
cd frontend
npm run build
```
Generates an optimized production bundle in `frontend/dist/`.

---

## API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/dashboard/` | Aggregated metrics (counts & Buddy status) |
| `GET`, `POST` | `/api/broadcasts/` | List and create campus announcements |
| `GET`, `POST` | `/api/schedules/` | List and schedule OneDrive links |
| `GET`, `PATCH` | `/api/settings/buddy/` | Retrieve and update Buddy exam availability |

*(User management and RAG document services are abstracted cleanly in `frontend/src/services/` with local persistence adapter patterns, ready for future backend endpoint integration).*
