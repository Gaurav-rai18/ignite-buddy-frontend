# Desktop shells: Electron and PySide6

The **UI** (React) and the **agent** (Python: device ops, STT, server link) are
the same in both cases. Only the **window host** changes.

```
                 ┌─────────────────────────┐
                 │  React UI (frontend/)   │
                 └───────────┬─────────────┘
                             │ loads from
                 ┌───────────▼─────────────┐
                 │  Local agent (Python)   │
                 │  127.0.0.1 — STT, device│
                 └───────────┬─────────────┘
                             │ hosted by ONE of
          ┌──────────────────┼──────────────────┐
          ▼                                     ▼
 ┌─────────────────┐                   ┌─────────────────┐
 │ PySide6 + Qt    │                   │ Electron        │
 │ WebEngine       │                   │ BrowserWindow   │
 │ pip .[desktop]  │                   │ npm install     │
 └─────────────────┘                   └─────────────────┘
```

## Choosing a shell

| Variable / command | Result |
|--------------------|--------|
| `ignite-desktop` | **auto** — Electron if `desktop-electron/node_modules` exists, else PySide6 |
| `ASSISTANT_SHELL=electron ignite-desktop` | Force Electron |
| `ASSISTANT_SHELL=pyside6 ignite-desktop` | Force PySide6 |
| `ignite-desktop --shell electron` | Same as env force |

## Setup

### PySide6 (default on locked-down Accops PCs)

**Bash / CMD:**
```bash
pip install -e .
cd frontend
npm run build
cd ..
ignite-desktop
```

### Electron (installer / web builds)

**Bash / CMD:**
```bash
pip install -e .
cd frontend
npm run build
cd ..
cd desktop-electron
npm install
ignite-desktop --shell electron
```

Produce installers (optional):

**Bash / CMD:**
```bash
cd desktop-electron
npm run dist      # NSIS / AppImage / dmg via electron-builder
```

The packaged app needs a working Python environment with `ignite-client` on `PATH` (or set `ASSISTANT_AGENT_CMD` to a wrapper script that starts the agent).

## Feature parity

| Feature | PySide6 | Electron |
|---------|---------|----------|
| Transparent always-on-top overlay | Yes | Yes |
| System tray | Yes | Yes |
| Global hotkey | Yes (`ASSISTANT_HOTKEY`) | Yes |
| Click-through outside UI | Yes (Qt mask regions) | Partial (`setIgnoreMouseEvents`; full region masks are limited) |
| Mic permission | Qt page grant | Chromium permission |
| Corporate “Python only” image | Best fit | Needs Node runtime or a prebuilt installer |

## Recommendation

* **Training lab / IT-managed Windows images** → PySide6.
* **Developers who already use Node, or you need `.exe` installers** → Electron.
* Keep **auto** for `trainee-desktop` so one command works in both environments.
