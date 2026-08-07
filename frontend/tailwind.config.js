/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0edff',
          100: '#ded9ff',
          500: '#6b5ce7',
          600: '#5140c7',
          700: '#392d91',
        },
        surface: {
          50: '#fbfaff',
          100: '#f3f2fa',
          200: '#e5e2f0',
        },
        ink: {
          700: '#514d68',
          800: '#2b2745',
          900: '#19172b',
        },
        status: {
          ok: '#087f6a',
          warn: '#a45a08',
          bad: '#c63b55',
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
