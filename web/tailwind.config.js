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
          bg: 'var(--ldvh-bg)',
          panel: 'var(--ldvh-panel)',
          border: 'var(--ldvh-border)',
          'text-primary': 'var(--ldvh-text-primary)',
          'text-secondary': 'var(--ldvh-text-secondary)',
          accent: '#00d4aa',
        },
      },
    },
  },
  plugins: [],
};
