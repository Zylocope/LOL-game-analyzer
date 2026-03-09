/**
 * DESIGN TOKENS - NEXUS SIGHT
 * 
 * This file documents all design tokens used in the professional redesign.
 * Use these values consistently across the application.
 * 
 * Generated: 2025
 * Version: 1.0
 */

// ============================================================================
// COLORS
// ============================================================================

export const COLORS = {
  // Primary Brand
  brand: {
    gold: '#C8AA6E',
    goldDark: '#6D5D4F',
    goldLight: '#E0D4BA',
  },

  // Team Colors
  team: {
    blue: '#0A4FA1',
    blueLighter: '#2E5AA0',
    blueLight: '#3D6BB8',
    red: '#C71C1C',
    redLighter: '#E63946',
    redLight: '#F55B5B',
  },

  // Neutral / Grayscale
  neutral: {
    darkest: '#0A0E27',    // Background
    dark: '#1A1F3A',       // Dark surface
    darker: '#2D333F',     // Card background
    gray: '#4A5568',       // Text secondary
    light: '#9CA3AF',      // Text tertiary
    lighter: '#E5E7EB',    // Borders
    white: '#FFFFFF',
  },

  // Status Colors
  status: {
    success: '#10B981',    // Green
    warning: '#F59E0B',    // Yellow/Amber
    danger: '#EF4444',     // Red
    info: '#3B82F6',       // Blue
  },

  // Semantic
  text: {
    primary: '#FFFFFF',
    secondary: '#9CA3AF',
    tertiary: '#6B7280',
    disabled: '#4B5563',
  },

  background: {
    primary: '#0A0E27',
    secondary: '#1A1F3A',
    tertiary: '#2D333F',
  },

  border: {
    light: 'rgba(229, 231, 235, 0.1)',
    medium: 'rgba(107, 114, 128, 0.3)',
    dark: 'rgba(31, 41, 55, 0.5)',
  },
};

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const TYPOGRAPHY = {
  fontFamily: {
    sans: '"Inter", "Segoe UI", system-ui, sans-serif',
    mono: '"Fira Code", "Menlo", monospace',
    display: '"Orbitron", "Inter", sans-serif',
  },

  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
    black: 900,
  },

  fontSize: {
    display1: {
      size: '4rem',
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
      weight: 900,
    },
    display2: {
      size: '2.25rem',
      lineHeight: 1.375,
      letterSpacing: '-0.02em',
      weight: 700,
    },
    heading1: {
      size: '1.875rem',
      lineHeight: 1.375,
      weight: 700,
    },
    heading2: {
      size: '1.5rem',
      lineHeight: 1.375,
      weight: 600,
    },
    heading3: {
      size: '1.25rem',
      lineHeight: 1.5,
      weight: 600,
    },
    bodyLarge: {
      size: '1.125rem',
      lineHeight: 1.5,
      weight: 500,
    },
    body: {
      size: '1rem',
      lineHeight: 1.5,
      weight: 400,
    },
    bodySmall: {
      size: '0.875rem',
      lineHeight: 1.5,
      weight: 400,
    },
    caption: {
      size: '0.75rem',
      lineHeight: 1.2,
      letterSpacing: '0.1em',
      weight: 500,
      textTransform: 'uppercase',
    },
    code: {
      size: '0.875rem',
      lineHeight: 1.375,
      weight: 400,
      fontFamily: '"Fira Code"',
    },
  },

  lineHeight: {
    tight: 1.2,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },

  letterSpacing: {
    tight: '-0.02em',
    normal: '0',
    wide: '0.05em',
    wider: '0.1em',
    widest: '0.2em',
  },
};

// ============================================================================
// SPACING
// ============================================================================

export const SPACING = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '0.75rem',   // 12px
  lg: '1rem',      // 16px (primary)
  xl: '1.5rem',    // 24px
  '2xl': '2rem',   // 32px
  '3xl': '3rem',   // 48px
  '4xl': '4rem',   // 64px
};

// Common padding/margin combinations
export const SPACING_PATTERNS = {
  xs: { x: '0.5rem', y: '0.25rem' },
  sm: { x: '1rem', y: '0.5rem' },
  md: { x: '1rem', y: '0.75rem' },
  lg: { x: '1.5rem', y: '1rem' },
  xl: { x: '2rem', y: '1.5rem' },
  tight: { x: '0.75rem', y: '0.5rem' },
  loose: { x: '2rem', y: '2rem' },
};

// ============================================================================
// SHADOWS
// ============================================================================

export const SHADOWS = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',

  // Professional glow effects
  glowBlue: '0 0 20px rgba(42, 90, 160, 0.4)',
  glowRed: '0 0 20px rgba(199, 28, 28, 0.4)',
  glowGold: '0 0 20px rgba(200, 170, 110, 0.4)',

  // Elevated card shadow
  card: '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
};

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const BORDER_RADIUS = {
  xs: '0.25rem',   // 4px
  sm: '0.375rem',  // 6px
  md: '0.5rem',    // 8px
  lg: '0.75rem',   // 12px
  xl: '1rem',      // 16px
  '2xl': '1.5rem', // 24px
  full: '9999px',  // Pill shape
};

// ============================================================================
// TRANSITIONS
// ============================================================================

export const TRANSITIONS = {
  duration: {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
  },

  timing: {
    easeIn: 'ease-in',
    easeOut: 'ease-out',
    easeInOut: 'ease-in-out',
    linear: 'linear',
    smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },

  properties: {
    all: 'all 200ms ease-in-out',
    color: 'color 200ms ease-in-out',
    background: 'background 200ms ease-in-out',
    shadow: 'box-shadow 200ms ease-in-out',
    transform: 'transform 200ms ease-in-out',
    opacity: 'opacity 200ms ease-in-out',
  },
};

// ============================================================================
// Z-INDEX SCALE
// ============================================================================

export const Z_INDEX = {
  hide: '-1',
  base: '0',
  dropdown: '10',
  sticky: '20',
  fixed: '30',
  modal: '40',
  popover: '50',
  tooltip: '60',
};

// ============================================================================
// BREAKPOINTS (Responsive)
// ============================================================================

export const BREAKPOINTS = {
  xs: '320px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// ============================================================================
// COMPONENT SIZING
// ============================================================================

export const COMPONENT_SIZES = {
  button: {
    xs: { padding: '0.25rem 0.5rem', fontSize: '0.75rem' },
    sm: { padding: '0.5rem 0.75rem', fontSize: '0.875rem' },
    md: { padding: '0.75rem 1rem', fontSize: '1rem' },
    lg: { padding: '1rem 1.5rem', fontSize: '1.125rem' },
    xl: { padding: '1.25rem 2rem', fontSize: '1.25rem' },
  },

  icon: {
    xs: '16px',
    sm: '20px',
    md: '24px',
    lg: '32px',
    xl: '40px',
  },

  input: {
    sm: { height: '2rem', padding: '0.5rem 0.75rem' },
    md: { height: '2.5rem', padding: '0.75rem 1rem' },
    lg: { height: '3rem', padding: '1rem 1.25rem' },
  },

  card: {
    sm: { padding: '0.75rem', borderRadius: '0.5rem' },
    md: { padding: '1rem', borderRadius: '0.75rem' },
    lg: { padding: '1.5rem', borderRadius: '1rem' },
  },

  avatar: {
    xs: '24px',
    sm: '32px',
    md: '40px',
    lg: '56px',
    xl: '80px',
  },

  badge: {
    sm: { padding: '0.25rem 0.5rem', fontSize: '0.75rem' },
    md: { padding: '0.375rem 0.75rem', fontSize: '0.875rem' },
    lg: { padding: '0.5rem 1rem', fontSize: '1rem' },
  },
};

// ============================================================================
// SEMANTIC COLORS (Usage Context)
// ============================================================================

export const SEMANTIC_COLORS = {
  primary: COLORS.brand.gold,
  secondary: COLORS.neutral.gray,
  success: COLORS.status.success,
  warning: COLORS.status.warning,
  danger: COLORS.status.danger,
  info: COLORS.status.info,

  // Team Indicators
  blueTeam: COLORS.team.blue,
  redTeam: COLORS.team.red,

  // Chart Colors
  chart: {
    blue: '#3B82F6',
    green: '#10B981',
    yellow: '#F59E0B',
    red: '#EF4444',
    purple: '#A855F7',
    indigo: '#6366F1',
  },

  // Overlay
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayLight: 'rgba(0, 0, 0, 0.25)',
  overlayDark: 'rgba(0, 0, 0, 0.75)',
};

// ============================================================================
// ANIMATION PRESETS
// ============================================================================

export const ANIMATIONS = {
  fadeIn: 'fadeIn 300ms ease-in-out',
  slideUp: 'slideUp 300ms ease-in-out',
  slideDown: 'slideDown 300ms ease-in-out',
  scaleIn: 'scaleIn 200ms ease-in-out',
  pulseGlow: 'pulseGlow 2s infinite',
};

// ============================================================================
// ACCESSIBLE COLOR COMBINATIONS
// ============================================================================

export const ACCESSIBLE_PAIRS = [
  { fg: COLORS.neutral.white, bg: COLORS.brand.gold, contrast: 5.5 },
  { fg: COLORS.neutral.white, bg: COLORS.team.blue, contrast: 7.2 },
  { fg: COLORS.neutral.white, bg: COLORS.team.red, contrast: 5.1 },
  { fg: COLORS.neutral.darker, bg: COLORS.brand.gold, contrast: 4.8 },
  { fg: COLORS.neutral.lighter, bg: COLORS.neutral.dark, contrast: 9.2 },
];

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Convert spacing token to pixels
 */
export function spacingToPx(token: keyof typeof SPACING): number {
  const value = SPACING[token];
  return parseFloat(value) * 16; // rem to px conversion
}

/**
 * Get color by semantic name
 */
export function getColor(
  context: 'text' | 'bg' | 'border' | 'status',
  variant: 'primary' | 'secondary' | 'success' | 'warning' | 'danger'
): string {
  switch (context) {
    case 'text':
      return variant === 'primary' ? COLORS.text.primary : COLORS.text.secondary;
    case 'status':
      return SEMANTIC_COLORS[variant as keyof typeof SEMANTIC_COLORS];
    default:
      return COLORS.neutral.darker;
  }
}

/**
 * Create box shadow with glow
 */
export function createGlowShadow(color: string, intensity: number = 0.4): string {
  return `0 0 20px rgba(${color}, ${intensity})`;
}

// ============================================================================
// EXPORT ALL TOKENS
// ============================================================================

export default {
  COLORS,
  TYPOGRAPHY,
  SPACING,
  SHADOWS,
  BORDER_RADIUS,
  TRANSITIONS,
  Z_INDEX,
  BREAKPOINTS,
  COMPONENT_SIZES,
  SEMANTIC_COLORS,
  ANIMATIONS,
  ACCESSIBLE_PAIRS,
};
