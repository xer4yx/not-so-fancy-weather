/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      keyframes: {
        spin: {
          '0%': { transform: 'rotate(360deg)' },
          '100%': { transform: 'rotate(0deg)' }
        }
      },
      animation: {
        'spin-steady': 'spin 20s linear infinite',
      }
    },
  },
  plugins: [
    require('tailwind-scrollbar-hide'),
  ],
}

