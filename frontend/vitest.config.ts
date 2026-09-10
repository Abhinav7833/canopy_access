import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: { environment: "jsdom", globals: true, setupFiles: ["./vitest.setup.ts"] },
  // fileURLToPath (not URL.pathname) so the alias is a real OS path even when the repo
  // lives under a directory with spaces on Windows (…/Abhinav Gupta/… -> no %20 breakage).
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
});
