import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages project site base
export default defineConfig({
  plugins: [react()],
  base: "/Network-Multi-Agent/",
  build: {
    outDir: "dist",
    // Sourcemaps blow CI memory with Plotly; enable locally via sourcemap=true if needed
    sourcemap: false,
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      output: {
        manualChunks: {
          plotly: ["plotly.js-basic-dist-min", "react-plotly.js"],
          viz: ["cytoscape", "cytoscape-fcose", "d3"],
          react: ["react", "react-dom", "react-router-dom", "framer-motion"],
        },
      },
    },
  },
});
