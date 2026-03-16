/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Space Grotesk", "Inter", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          primary: "#38bdf8",
          accent: "#f472b6",
          warning: "#fbbf24",
        },
      },
    },
  },
  plugins: [],
};
