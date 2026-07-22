import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Собранные файлы уезжают в web/static/dist — FastAPI отдаёт их как обычную статику
// (см. web/main.py), поэтому base совпадает с тем, куда их монтирует StaticFiles.
export default defineConfig({
  plugins: [react()],
  base: "/static/dist/",
  build: {
    outDir: "../static/dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/auth": "http://localhost:8000",
      "/logout": "http://localhost:8000",
      "/media": "http://localhost:8000",
    },
  },
});
