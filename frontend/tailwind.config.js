/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter var', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        // Deep ocean blue: the primary brand ramp.
        abyss: {
          50: '#f0f7fb',
          100: '#dcecf6',
          200: '#bcdaed',
          300: '#8dc0df',
          400: '#569ecb',
          500: '#3281b3',
          600: '#236897',
          700: '#1d547b',
          800: '#1c4766',
          900: '#0f2e45',
          950: '#0a1c2b',
        },
        // Warm signal ramp for severity.
        signal: {
          low: '#0d9488',
          medium: '#d97706',
          high: '#dc2626',
        },
      },
      boxShadow: {
        card: '0 1px 2px 0 rgb(15 46 69 / 0.04), 0 1px 3px 0 rgb(15 46 69 / 0.06)',
        lift: '0 10px 30px -12px rgb(15 46 69 / 0.18), 0 4px 10px -6px rgb(15 46 69 / 0.10)',
        glow: '0 0 0 3px rgb(86 158 203 / 0.16)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateX(12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.7)', opacity: '0.7' },
          '80%, 100%': { transform: 'scale(2.2)', opacity: '0' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        'sweep': {
          '0%': { strokeDashoffset: 'var(--dash)' },
        },
        'drift': {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
      },
      animation: {
        'fade-up': 'fade-up .45s cubic-bezier(.16,1,.3,1) both',
        'slide-in': 'slide-in .4s cubic-bezier(.16,1,.3,1) both',
        'pulse-ring': 'pulse-ring 2.4s cubic-bezier(.24,.6,.35,1) infinite',
        shimmer: 'shimmer 1.8s infinite',
        drift: 'drift 6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
