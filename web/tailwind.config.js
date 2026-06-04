/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        ldvh: {
          bg: '#0a0a0f',
          panel: '#12121a',
          border: '#1e1e2e',
          'text-primary': '#e4e4e7',
          'text-secondary': '#71717a',
          accent: '#00d4aa',
        },
      },
    },
  },
  plugins: [],
};
