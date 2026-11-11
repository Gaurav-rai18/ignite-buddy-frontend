# Trainee Assistant UI (`frontend`)

The lightweight, interactive desktop overlay interface for **Trainees** in the TCS Ignite Program. Built with **React 18**, **Three.js** (for 3D mascot rendering), and **Lucide React** icons.

---

## Features

- **3D Animated Avatar**: Interactive GLTF/GLB mascot (`Avatar3D`) that visually responds to listening, thinking, speaking, and idle states.
- **Dynamic Bubble UI**: Voice and text input bubble that expands smoothly when receiving queries or displaying actions.
- **AnswerModal**: Rich modal presentation for answers, internal policy references, and directory navigation with clickable file items.
- **Voice Input**:
  - One-shot audio recording sent directly to the server for transcription (no local STT model downloads).
  - VAD (Voice Activity Detection) and automatic mic timeout.
  - Strictly no emojis: uses accessible `lucide-react` icons throughout.
- **Real-Time Push Notifications**: Receives instant toast announcements sent by instructors from the Admin Console.

---

## Build & Integration

The Vite build is configured to compile directly into the local Python client's static directory (`src/client/agent/static/`):

**Bash / CMD:**
```bash
# Install frontend dependencies
npm install

# Build production bundle into src/client/agent/static/
npm run build
```

During development with hot reload:

**Bash / CMD:**
```bash
npm run dev
# Proxies WebSocket and agent calls to http://127.0.0.1:8777
```

