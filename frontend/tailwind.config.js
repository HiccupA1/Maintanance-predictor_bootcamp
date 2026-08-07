/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f3ff',
          100: '#ede9fe',
          500: '#7c3aed',
          600: '#6d28d9',
          700: '#5b21b6',
        },
        surface: {
          50: 'rgba(255,255,255,0.06)',
          100: 'rgba(255,255,255,0.08)',
          200: 'rgba(255,255,255,0.10)',
        },
        ink: {
          700: 'rgba(255,255,255,0.72)',
          800: 'rgba(255,255,255,0.84)',
          900: 'rgba(255,255,255,0.92)',
        },
        status: {
          ok: '#10b981',
          warn: '#f59e0b',
          bad: '#fb7185',
        },
      },
      boxShadow: {
        card: '0 10px 40px rgba(0, 0, 0, 0.45)',
      },
      borderRadius: {
        ui: '1rem',
      },
    },
  },
  plugins: [],
};
