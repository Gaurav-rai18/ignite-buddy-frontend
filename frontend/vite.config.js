import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The build goes straight into the Python agent, which serves it. Corporate laptops need only Python, not Node.
export default defineConfig({
  plugins: [react()],
  build: { chunkSizeWarningLimit: 900, outDir: "../src/client/agent/static", emptyOutDir: true },
  server: { proxy: { "/ws": { target: "ws://127.0.0.1:8777", ws: true } } },
});
