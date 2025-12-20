/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        // ChatterFix brand colors
        primary: {
          DEFAULT: "#00d4ff",
          dark: "#0099cc",
        },
        background: {
          DEFAULT: "#1a1a2e",
          card: "#16213e",
        },
        accent: "#ff6b35",
        success: "#00c853",
        warning: "#ffc107",
        danger: "#ff3d00",
      },
    },
  },
  plugins: [],
};
