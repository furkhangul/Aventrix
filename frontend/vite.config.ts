import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    watch: {
      // Native fs events from a Windows bind mount often don't reach
      // chokidar inside the Linux container, which silently freezes HMR —
      // polling guarantees changes are picked up regardless of host OS.
      // 1s is plenty responsive for dev and far lighter than the earlier
      // 300ms, which was stat-ing the whole tree 3x/sec and adding
      // noticeable load to the dev server under Docker on Windows.
      usePolling: true,
      interval: 1000,
    },
    proxy: {
      "/api": {
        target: process.env.DEV_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
        bypass(req) {
          // Prefix matching means "/api" would otherwise also swallow SPA
          // routes that merely start with those letters (e.g. /api-keys) —
          // only proxy real API calls, which always start with "/api/".
          const path = (req.url || "").split("?")[0];
          if (path !== "/api" && !path.startsWith("/api/")) {
            return "/index.html";
          }
        },
      },
      "/t": {
        target: process.env.DEV_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
        bypass(req) {
          // /t/{code}/gate and /t/not-found are SPA pages (React Router),
          // not backend routes — serve index.html instead of proxying.
          const path = (req.url || "").split("?")[0];
          if (path === "/t/not-found" || /^\/t\/[^/]+\/gate$/.test(path)) {
            return "/index.html";
          }
        },
      },
      "/uploads": {
        target: process.env.DEV_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./tests/setup.ts",
  },
});
