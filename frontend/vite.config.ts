import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Points at the repo-level shared/ contract types so the frontend
      // and backend stay aligned on one source of truth instead of a
      // copy-pasted duplicate living inside frontend/.
      "@shared": path.resolve(__dirname, "../shared"),
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
  },
});
