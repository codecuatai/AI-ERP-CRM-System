/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../crm/templates/**/*.html", "../crm/**/*.py"],
  theme: {
    extend: {
      colors: {
        canvas: "#f5f6f8",
        ink: "#20252d",
        muted: "#858d99",
        brand: "#625bf6",
        line: "#e9ebef",
      },
      boxShadow: {
        card: "0 2px 10px rgba(25, 34, 48, .035)",
        float: "0 12px 32px rgba(25, 34, 48, .12)",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};
