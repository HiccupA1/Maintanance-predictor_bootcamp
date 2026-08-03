/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef4ff',
          100: '#d9e5ff',
          500: '#3b6df5',
          600: '#2f57c9',
          700: '#26469f',
        },
        surface: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
        },
        ink: {
          700: '#334155',
          800: '#1f2937',
          900: '#0f172a',
        },
        status: {
          ok: '#15803d',
          warn: '#b45309',
          bad: '#b91c1c',
        },
      },
      boxShadow: {
        card: '0 1px 2px rgba(15, 23, 42, 0.06)',
      },
      borderRadius: {
        ui: '0.5rem',
      },
    },
  },
  plugins: [],
};
