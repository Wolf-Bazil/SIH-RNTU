/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        maritime: {
          900: '#0a1929',
          800: '#0d2137',
          700: '#132f4c',
          600: '#1a3a5c',
          500: '#265d97',
          400: '#5090d3',
          300: '#7ab8f5',
          200: '#a5d8ff',
          100: '#d0ebff',
        }
      }
    },
  },
  plugins: [],
}
