/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark Fantasy Theme
        background: {
          DEFAULT: '#0f0f17',
          secondary: '#1a1a2e',
          tertiary: '#16213e',
        },
        primary: {
          DEFAULT: '#d4a437',
          light: '#e6c065',
          dark: '#b8892a',
        },
        secondary: {
          DEFAULT: '#8b2252',
          light: '#a83a6a',
          dark: '#6d1a40',
        },
        accent: {
          DEFAULT: '#4a7fb5',
          light: '#6899c7',
          dark: '#3a6a9a',
        },
        text: {
          DEFAULT: '#e8dcc8',
          muted: '#a89f8f',
          dark: '#7a7268',
        },
        success: '#4ade80',
        warning: '#fbbf24',
        danger: '#ef4444',
        info: '#60a5fa',
        // Mood colors
        mood: {
          tense: '#dc2626',
          calm: '#3b82f6',
          mysterious: '#8b5cf6',
          triumphant: '#f59e0b',
          somber: '#6b7280',
          humorous: '#10b981',
          urgent: '#f97316',
          peaceful: '#06b6d4',
        },
      },
      fontFamily: {
        heading: ['Cinzel', 'Cormorant Garamond', 'serif'],
        body: ['Crimson Text', 'Spectral', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-primary': '0 0 20px rgba(212, 164, 55, 0.3)',
        'glow-secondary': '0 0 20px rgba(139, 34, 82, 0.3)',
        'glow-accent': '0 0 20px rgba(74, 127, 181, 0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'dice-roll': 'diceRoll 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(212, 164, 55, 0.3)' },
          '50%': { boxShadow: '0 0 30px rgba(212, 164, 55, 0.5)' },
        },
        diceRoll: {
          '0%': { transform: 'rotate(0deg) scale(1)' },
          '50%': { transform: 'rotate(180deg) scale(1.2)' },
          '100%': { transform: 'rotate(360deg) scale(1)' },
        },
      },
      backgroundImage: {
        'parchment': "url('/textures/parchment.png')",
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
};
