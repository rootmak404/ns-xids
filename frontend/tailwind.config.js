/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0A0E14",
        panel: "#12161F",
        panel2: "#171C27",
        border: "#232838",
        text: "#E4E7EE",
        muted: "#7C8494",
        signal: "#2DD4BF",
        low: "#4ADE80",
        medium: "#FBBF24",
        high: "#FB923C",
        critical: "#F87171",
      },
      fontFamily: {
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
