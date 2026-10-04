import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: { port: 5173, strictPort: true, proxy: { "/api": { target: mode === "e2e" ? "http://127.0.0.1:8011" : "http://127.0.0.1:8010", ws: true } } },
  test: { include: ["tests/**/*.test.{ts,tsx}"], environment: "jsdom", setupFiles: "./tests/setup.ts", globals: true },
}));
