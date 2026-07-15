/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Investigation palette — dark HQ with evidence signal colors
        hq: { bg: "#0b0f1a", panel: "#141a2b", edge: "#1f2940" },
        signal: { high: "#34d399", mid: "#fbbf24", low: "#64748b", contra: "#f43f5e" },
      },
    },
  },
  plugins: [],
};
