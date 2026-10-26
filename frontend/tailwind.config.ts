/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./App.tsx",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // === COLORS ===
      colors: {
        // Brand
        'esport-gold': '#C8AA6E',
        'esport-gold-dark': '#6D5D4F',
        'esport-gold-light': '#E0D4BA',

        // Team Colors
        'esport-blue': '#0A4FA1',
        'esport-blue-light': '#2E5AA0',
        'esport-blue-lighter': '#3D6BB8',
        'esport-red': '#C71C1C',
        'esport-red-light': '#E63946',
        'esport-red-lighter': '#F55B5B',

        // Grayscale
        'esport-dark': '#0A0E27',
        'esport-darker': '#1A1F3A',
        'esport-gray': '#2D333F',
        'esport-gray-light': '#4A5568',
      },

      // === TYPOGRAPHY ===
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'Menlo', 'monospace'],
        display: ['Orbitron', 'Inter', 'sans-serif'],
      },

      fontSize: {
        'display-1': ['4rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
        'display-2': ['2.25rem', { lineHeight: '1.375', letterSpacing: '-0.02em' }],
        'heading-1': ['1.875rem', { lineHeight: '1.375' }],
        'heading-2': ['1.5rem', { lineHeight: '1.375' }],
        'heading-3': ['1.25rem', { lineHeight: '1.5' }],
        'body-lg': ['1.125rem', { lineHeight: '1.5' }],
        'body': ['1rem', { lineHeight: '1.5' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        'caption': ['0.75rem', { lineHeight: '1.2', letterSpacing: '0.1em' }],
      },

      fontWeight: {
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
        black: '900',
      },

      lineHeight: {
        tight: '1.2',
        snug: '1.375',
        normal: '1.5',
        relaxed: '1.625',
        loose: '2',
      },

      letterSpacing: {
        tight: '-0.02em',
        normal: '0',
        wide: '0.05em',
        wider: '0.1em',
        widest: '0.2em',
      },

      // === SPACING ===
      spacing: {
        xs: '0.25rem',
        sm: '0.5rem',
        md: '0.75rem',
        lg: '1rem',
        xl: '1.5rem',
        '2xl': '2rem',
        '3xl': '3rem',
        '4xl': '4rem',
      },

      // === SHADOWS ===
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'base': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',

        // Professional glow effects
        'glow-blue': '0 0 20px rgba(42, 90, 160, 0.4)',
        'glow-red': '0 0 20px rgba(199, 28, 28, 0.4)',
        'glow-gold': '0 0 20px rgba(200, 170, 110, 0.4)',

        // Elevated card shadow
        'card': '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
      },

      // === BORDER RADIUS ===
      borderRadius: {
        'xs': '0.25rem',
        'sm': '0.375rem',
        'md': '0.5rem',
        'lg': '0.75rem',
        'xl': '1rem',
        '2xl': '1.5rem',
        'full': '9999px',
      },

      // === TRANSITIONS ===
      transitionDuration: {
        'fast': '150ms',
        'base': '200ms',
        'slow': '300ms',
      },

      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },

      // === ANIMATIONS ===
      animation: {
        'fade-in': 'fadeIn 300ms ease-in-out',
        'slide-up': 'slideUp 300ms ease-in-out',
        'slide-down': 'slideDown 300ms ease-in-out',
        'scale-in': 'scaleIn 200ms ease-in-out',
        'pulse-glow': 'pulseGlow 2s infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': {
            opacity: '0',
            transform: 'translateY(10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        slideDown: {
          '0%': {
            opacity: '0',
            transform: 'translateY(-10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        scaleIn: {
          '0%': {
            opacity: '0',
            transform: 'scale(0.95)',
          },
          '100%': {
            opacity: '1',
            transform: 'scale(1)',
          },
        },
        pulseGlow: {
          '0%, 100%': {
            boxShadow: '0 0 0 0 rgba(200, 170, 110, 0.7)',
          },
          '50%': {
            boxShadow: '0 0 0 10px rgba(200, 170, 110, 0)',
          },
        },
      },

      // === BACKDROP ===
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        base: '8px',
        md: '12px',
        lg: '16px',
      },

      // === GRADIENTS ===
      backgroundImage: {
        'gradient-gold': 'linear-gradient(135deg, #E0D4BA, #C8AA6E)',
        'gradient-team': 'linear-gradient(135deg, #0A4FA1, #C71C1C)',
        'gradient-blue-red': 'linear-gradient(to right, rgba(10, 79, 161, 0.2), rgba(199, 28, 28, 0.2))',
      },
    },
  },

  plugins: [
    // Professional rounded corners
    function ({ addUtilities }) {
      const newUtilities = {
        '.glass-effect': {
          '@apply': 'backdrop-blur-md bg-opacity-60 border border-opacity-10',
          backgroundColor: 'rgba(26, 31, 58, 0.6)',
          borderColor: 'rgba(229, 231, 235, 0.1)',
        },
        '.card-elevated': {
          '@apply': 'bg-esport-gray border border-opacity-10 rounded-lg shadow-lg transition-all',
          backgroundColor: '#2D333F',
          borderColor: 'rgba(229, 231, 235, 0.1)',
        },
        '.card-elevated:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
        },
        '.btn-primary': {
          '@apply': 'px-4 py-2 bg-esport-gold text-black font-bold rounded-lg transition-all hover:shadow-glow-gold',
        },
        '.btn-secondary': {
          '@apply': 'px-4 py-2 bg-esport-gray border border-opacity-10 text-gray-200 font-semibold rounded-lg transition-all hover:border-esport-gold hover:text-esport-gold',
        },
        '.text-gradient-gold': {
          '@apply': 'bg-clip-text text-transparent',
          backgroundImage: 'linear-gradient(135deg, #E0D4BA, #C8AA6E)',
        },
        '.text-gradient-team': {
          '@apply': 'bg-clip-text text-transparent',
          backgroundImage: 'linear-gradient(135deg, #0A4FA1, #C71C1C)',
        },
        '.outline-blue': {
          '@apply': 'border-2 border-esport-blue rounded-lg transition-all hover:shadow-glow-blue',
        },
        '.outline-red': {
          '@apply': 'border-2 border-esport-red rounded-lg transition-all hover:shadow-glow-red',
        },
      };
      addUtilities(newUtilities);
    },
  ],
};
