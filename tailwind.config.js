/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        atlas: {
          bg: "#0A0F1F",
          accent: "#2A7DE1"
        }
      }
    }
  },
  plugins: []
};
