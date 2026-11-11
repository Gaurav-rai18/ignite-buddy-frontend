/**
 * Preload bridge: the React page talks to the local Python agent over WebSocket
 * as usual. This bridge only exposes shell capabilities Electron must handle
 * (hit-testing / click-through, quit).
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronShell", {
  setHitRects: (rects) => ipcRenderer.send("shell-hit", rects),
  hide: () => ipcRenderer.send("shell-hide"),
  quit: () => ipcRenderer.send("shell-quit"),
  onActivate: (cb) => ipcRenderer.on("shell-activate", () => cb()),
  onDeactivate: (cb) => ipcRenderer.on("shell-deactivate", () => cb()),
  isElectron: true,
});
