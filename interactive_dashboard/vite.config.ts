import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages project site base
export default defineConfig({
  plugins: [react()],
  base: "/Network-Multi-Agent/",
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
