/**
 * Electron overlay shell for Trainee Assistant.
 *
 * Same product role as the PySide6 shell:
 *   - start (or attach to) the local Python agent
 *   - transparent always-on-top window loading the agent UI
 *   - global shortcut to summon / dismiss
 *   - system tray
 *   - click-through except where the page reports hit rects
 *
 * The Python agent still owns device ops, STT, and the central-server WebSocket.
 * Electron only hosts the Chromium view and OS integration.
 */
const { app, BrowserWindow, globalShortcut, Tray, Menu, nativeImage, ipcMain, screen } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");

const WIN_W = 780;
const WIN_H = 860;
const HOTKEY = process.env.ASSISTANT_HOTKEY || "CommandOrControl+Alt+Space";
const AGENT_HOST = "127.0.0.1";
const AGENT_PORT = parseInt(process.env.ASSISTANT_AGENT_PORT || "8777", 10);

let mainWindow = null;
let tray = null;
let agentProc = null;
let agentUrl = null;
let active = false;
let hitRects = [];

// ---------- agent lifecycle ----------

function agentBase() {
  return `http://${AGENT_HOST}:${AGENT_PORT}`;
}

function waitForAgent(timeoutMs = 20000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const tryOnce = () => {
      const req = http.get(`${agentBase()}/`, (res) => {
        res.resume();
        resolve(`${agentBase()}/`);
      });
      req.on("error", () => {
        if (Date.now() - start > timeoutMs) reject(new Error("Local agent did not start in time"));
        else setTimeout(tryOnce, 300);
      });
      req.setTimeout(500, () => {
        req.destroy();
        if (Date.now() - start > timeoutMs) reject(new Error("Local agent did not start in time"));
        else setTimeout(tryOnce, 300);
      });
    };
    tryOnce();
  });
}

function startAgent() {
  // Launch the local agent server process.
  // Attempts to launch `trainee-agent` from the system PATH first. On Windows (such as
  // Accops VDI environments) where shell execution may exit immediately with a non-zero code
  // rather than emitting an 'error' event when a command is missing, automatically triggers
  // a fallback to `python -m assistant_client.agent.server`.
  const env = {
    ...process.env,
    ASSISTANT_AGENT_PORT: String(AGENT_PORT),
  };
  const cmd = process.env.ASSISTANT_AGENT_CMD;
  if (cmd) {
    agentProc = spawn(cmd, { env, shell: true, stdio: "inherit" });
    agentProc.on("exit", (code) => {
      console.log(`[electron] agent exited (${code})`);
    });
    return;
  }

  let fallbackStarted = false;
  const launchFallback = () => {
    if (fallbackStarted) return;
    fallbackStarted = true;
    console.log("[electron] Falling back to python -m assistant_client.agent.server");
    agentProc = spawn(process.env.PYTHON || "python", ["-m", "assistant_client.agent.server", "--port", String(AGENT_PORT), "--no-browser"], {
      env,
      stdio: "inherit",
      shell: process.platform === "win32",
    });
    agentProc.on("exit", (code) => {
      console.log(`[electron] agent exited (${code})`);
    });
  };

  const spawnTimestamp = Date.now();
  agentProc = spawn("trainee-agent", ["--port", String(AGENT_PORT), "--no-browser"], {
    env,
    stdio: "inherit",
    shell: process.platform === "win32",
  });

  agentProc.on("error", () => {
    launchFallback();
  });

  agentProc.on("exit", (code) => {
    console.log(`[electron] agent exited (${code})`);
    // Detect fast failure on Windows where shell: true exits with non-zero without 'error'
    if (code !== 0 && Date.now() - spawnTimestamp < 1500 && !fallbackStarted) {
      launchFallback();
    }
  });
}

function stopAgent() {
  if (agentProc && !agentProc.killed) {
    try {
      agentProc.kill();
    } catch (_) {}
  }
  agentProc = null;
}

// ---------- window / click-through ----------

function applyClickThrough() {
  if (!mainWindow) return;
  // When no interactive regions, ignore all mouse events (click-through).
  // When we have rects, we still use ignore+forward and rely on the page's
  // own hit targets; full region masking is OS-specific and limited in Electron.
  const hasHits = hitRects.length > 0;
  if (!hasHits) {
    mainWindow.setIgnoreMouseEvents(true, { forward: true });
  } else {
    // Allow interaction; the transparent areas of the page still pass events
    // when the window uses a transparent background on supported platforms.
    mainWindow.setIgnoreMouseEvents(false);
  }
}

function createWindow(url) {
  const display = screen.getPrimaryDisplay().workArea;
  const x = display.x + display.width - WIN_W - 12;
  const y = display.y + display.height - WIN_H - 12;

  mainWindow = new BrowserWindow({
    width: WIN_W,
    height: WIN_H,
    x,
    y,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    hasShadow: false,
    show: false,
    backgroundColor: "#00000000",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      // Microphone for the local agent page
      sandbox: false,
    },
  });

  mainWindow.setAlwaysOnTop(true, "screen-saver");
  mainWindow.loadURL(url);
  mainWindow.once("ready-to-show", () => {
    mainWindow.showInactive();
    applyClickThrough();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function summon() {
  if (!mainWindow) return;
  if (mainWindow.isVisible() && active) {
    mainWindow.hide();
    active = false;
    mainWindow.webContents.send("shell-deactivate");
  } else {
    mainWindow.setAlwaysOnTop(true, "screen-saver");
    mainWindow.show();
    mainWindow.focus();
    active = true;
    mainWindow.webContents.send("shell-activate");
  }
}

function createTray() {
  // 16x16 blue circle as a simple tray icon
  const img = nativeImage.createEmpty();
  tray = new Tray(nativeImage.createFromDataURL(
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAMUlEQVQ4T2NkYGD4z0ABYBzVMKoBBgYGRgYGhv8gNYwMjIwMjP8ZGRgYGAlqAKn+GQYAAf0EAaY0nHkAAAAASUVORK5CYII="
  ));
  const menu = Menu.buildFromTemplate([
    { label: `Talk (${HOTKEY})`, click: () => summon() },
    {
      label: "Show / hide",
      click: () => {
        if (!mainWindow) return;
        if (mainWindow.isVisible()) mainWindow.hide();
        else {
          mainWindow.show();
          mainWindow.focus();
        }
      },
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        app.quit();
      },
    },
  ]);
  tray.setToolTip("Trainee Assistant");
  tray.setContextMenu(menu);
  tray.on("click", () => summon());
}

// ---------- IPC from preload / page ----------

ipcMain.on("shell-hit", (_e, rects) => {
  hitRects = Array.isArray(rects) ? rects : [];
  applyClickThrough();
});
ipcMain.on("shell-hide", () => {
  mainWindow?.hide();
  active = false;
});
ipcMain.on("shell-quit", () => app.quit());

// ---------- app lifecycle ----------

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    startAgent();
    try {
      agentUrl = await waitForAgent();
    } catch (e) {
      console.error("[electron]", e.message);
      console.error("Is the client installed?  pip install -e \".[client]\"  then ensure trainee-agent works.");
      app.quit();
      return;
    }
    createWindow(agentUrl);
    createTray();
    const ok = globalShortcut.register(HOTKEY, () => summon());
    if (!ok) console.warn(`[electron] could not register hotkey ${HOTKEY}`);
    console.log(`[electron] running. Shortcut: ${HOTKEY}  UI: ${agentUrl}`);
  });

  app.on("will-quit", () => {
    globalShortcut.unregisterAll();
    stopAgent();
  });

  app.on("window-all-closed", (e) => {
    // keep tray app alive
    e.preventDefault();
  });
}
