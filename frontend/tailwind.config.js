/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        teal: '#016764',
        gold: '#B8904A',
        burgundy: '#7A1E47',
        cream: '#FAF8F4',
        ink: '#1A1612'
      },
      fontFamily: {
        body: ['Outfit', 'sans-serif'],
        heading: ['Cormorant Garamond', 'serif'],
        mono: ['JetBrains Mono', 'monospace']
      },
      spacing: {
        1: '4px',
        2: '8px',
        3: '12px',
        4: '16px',
        5: '20px',
        6: '24px',
        8: '32px',
        10: '40px',
        12: '48px',
        16: '64px',
        20: '80px',
        24: '96px'
      }
    }
  },
  plugins: []
};