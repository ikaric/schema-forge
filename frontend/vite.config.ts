import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, the Vite server proxies the API + WebSocket to the FastAPI backend on
// :8000, so the UI behaves identically to the production build that the backend
// serves directly. In prod, `npm run build` emits the SPA into the backend's
// static dir, served on http://127.0.0.1:8000.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../backend/src/schema_forge/static",
    emptyOutDir: true,
    // Plotly is a large single dependency; the gzipped payload is fine for a
    // localhost app, so don't warn about the chunk size.
    chunkSizeWarningLimit: 5000,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
});
