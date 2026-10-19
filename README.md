# TCS-themed Admin Console — Project Demo

A TCS-branded visual theme for an independent demo project built with React, Django REST Framework, and SQLite. This is **not an official Tata Consultancy Services product or an affiliated service**. Branding is used for a project/demo presentation only.

## Features
- Responsive admin dashboard
- Broadcast announcement creation and history
- OneDrive link scheduling form
- Buddy ON/OFF setting saved through the backend
- TCS-themed wordmark and subtle watermark
- Django API with SQLite storage

## Requirements
- Python 3.10+
- Node.js 18+

## Start backend (Windows)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
API runs at `http://127.0.0.1:8000/api/`.

## Start frontend (new terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open the local URL printed by Vite (usually `http://localhost:5173`).

## Notes before production
This is a development demo. Add Django authentication and API permissions before deployment. Scheduled entries are stored with their intended publish time, but automatic background publishing and delivery to a student dashboard require a scheduler and a connected student-facing application. The Buddy toggle currently stores the setting in this app; connecting it to a separate Buddy service requires that service's API.
