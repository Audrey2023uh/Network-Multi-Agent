/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        noc: {
          bg: "#0B1220",
          panel: "#121A2B",
          border: "#1E2A44",
          accent: "#1F7A8C",
          accent2: "#4A90A4",
          amber: "#C47B2B",
          text: "#E8EEF4",
          muted: "#8BA0B8",
        },
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
