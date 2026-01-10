/**
 * Lexecon Design System - Design Tokens
 *
 * Enterprise AI Governance Platform
 * Version: 1.0.0
 * Last Updated: 2026-01-10
 *
 * These tokens define the foundational design decisions for the Lexecon platform.
 * Use these tokens consistently across all components and screens.
 */

export const tokens = {
  // ============================================================================
  // COLOR SYSTEM
  // ============================================================================

  colors: {
    // Brand Colors - Professional, trustworthy, authoritative
    brand: {
      primary: {
        50: '#EEF2FF',   // Lightest - backgrounds, hover states
        100: '#E0E7FF',
        200: '#C7D2FE',
        300: '#A5B4FC',
        400: '#818CF8',
        500: '#6366F1',  // Primary brand color - main CTAs, links
        600: '#4F46E5',  // Hover states
        700: '#4338CA',  // Active states
        800: '#3730A3',
        900: '#312E81',  // Darkest - text on light backgrounds
        950: '#1E1B4B'
      },
      secondary: {
        50: '#F0FDFA',
        100: '#CCFBF1',
        200: '#99F6E4',
        300: '#5EEAD4',
        400: '#2DD4BF',
        500: '#14B8A6',  // Secondary brand - success states, accents
        600: '#0D9488',
        700: '#0F766E',
        800: '#115E59',
        900: '#134E4A',
        950: '#042F2E'
      }
    },

    // Neutral Colors - UI backgrounds, borders, text
    neutral: {
      0: '#FFFFFF',     // Pure white
      50: '#FAFAFA',    // Off-white backgrounds
      100: '#F5F5F5',   // Card backgrounds, subtle fills
      200: '#E5E5E5',   // Borders, dividers
      300: '#D4D4D4',   // Disabled borders
      400: '#A3A3A3',   // Placeholder text
      500: '#737373',   // Secondary text
      600: '#525252',   // Body text
      700: '#404040',   // Headings
      800: '#262626',   // Strong emphasis
      900: '#171717',   // Darkest text
      950: '#0A0A0A'    // Maximum contrast
    },

    // Semantic Colors - States and feedback
    semantic: {
      // Success - Approvals, confirmations, positive states
      success: {
        50: '#F0FDF4',
        100: '#DCFCE7',
        200: '#BBF7D0',
        300: '#86EFAC',
        400: '#4ADE80',
        500: '#22C55E',   // Primary success
        600: '#16A34A',
        700: '#15803D',
        800: '#166534',
        900: '#14532D'
      },

      // Warning - Escalations, pending approvals, attention needed
      warning: {
        50: '#FFFBEB',
        100: '#FEF3C7',
        200: '#FDE68A',
        300: '#FCD34D',
        400: '#FBBF24',
        500: '#F59E0B',   // Primary warning
        600: '#D97706',
        700: '#B45309',
        800: '#92400E',
        900: '#78350F'
      },

      // Error - Denials, failures, critical issues
      error: {
        50: '#FEF2F2',
        100: '#FEE2E2',
        200: '#FECACA',
        300: '#FCA5A5',
        400: '#F87171',
        500: '#EF4444',   // Primary error
        600: '#DC2626',
        700: '#B91C1C',
        800: '#991B1B',
        900: '#7F1D1D'
      },

      // Info - Informational states, tips, guidance
      info: {
        50: '#EFF6FF',
        100: '#DBEAFE',
        200: '#BFDBFE',
        300: '#93C5FD',
        400: '#60A5FA',
        500: '#3B82F6',   // Primary info
        600: '#2563EB',
        700: '#1D4ED8',
        800: '#1E40AF',
        900: '#1E3A8A'
      }
    },

    // Data Visualization - Charts, graphs, metrics
    dataViz: {
      // Categorical - For different categories in charts
      categorical: {
        1: '#6366F1',  // Primary brand
        2: '#14B8A6',  // Secondary brand
        3: '#F59E0B',  // Warning
        4: '#EF4444',  // Error
        5: '#3B82F6',  // Info
        6: '#8B5CF6',  // Purple
        7: '#EC4899',  // Pink
        8: '#10B981',  // Green
        9: '#F97316',  // Orange
        10: '#06B6D4'  // Cyan
      },

      // Sequential - For heatmaps, gradients (low to high risk)
      sequential: {
        1: '#EEF2FF',  // Lowest risk
        2: '#C7D2FE',
        3: '#A5B4FC',
        4: '#818CF8',
        5: '#6366F1',
        6: '#4F46E5',
        7: '#4338CA',
        8: '#3730A3',
        9: '#312E81',  // Highest risk
      },

      // Risk Scale - Specific to risk assessment
      risk: {
        minimal: '#22C55E',    // Green
        low: '#84CC16',        // Lime
        medium: '#F59E0B',     // Amber
        high: '#F97316',       // Orange
        critical: '#EF4444'    // Red
      }
    },

    // Governance-Specific Colors
    governance: {
      // Policy states
      policy: {
        active: '#22C55E',
        draft: '#94A3B8',
        deprecated: '#F59E0B',
        archived: '#64748B'
      },

      // Decision outcomes
      decision: {
        approved: '#22C55E',
        denied: '#EF4444',
        escalated: '#F59E0B',
        pending: '#3B82F6',
        override: '#8B5CF6'
      },

      // Compliance status
      compliance: {
        compliant: '#22C55E',
        nonCompliant: '#EF4444',
        partialCompliant: '#F59E0B',
        notAssessed: '#94A3B8'
      }
    }
  },

  // ============================================================================
  // TYPOGRAPHY SYSTEM
  // ============================================================================

  typography: {
    // Font Families
    fontFamily: {
      sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
      mono: "'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace",
      display: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    },

    // Font Sizes - Based on modular scale (1.250 - Major Third)
    fontSize: {
      xs: '0.75rem',      // 12px - Captions, labels
      sm: '0.875rem',     // 14px - Small text, secondary info
      base: '1rem',       // 16px - Body text, default
      lg: '1.125rem',     // 18px - Large body, subheadings
      xl: '1.25rem',      // 20px - Section headings
      '2xl': '1.5rem',    // 24px - Page headings
      '3xl': '1.875rem',  // 30px - Major headings
      '4xl': '2.25rem',   // 36px - Display headings
      '5xl': '3rem',      // 48px - Hero headings
      '6xl': '3.75rem',   // 60px - Large displays
      '7xl': '4.5rem',    // 72px - Extra large displays
    },

    // Font Weights
    fontWeight: {
      thin: 100,
      extralight: 200,
      light: 300,
      normal: 400,      // Body text
      medium: 500,      // Emphasis, buttons
      semibold: 600,    // Subheadings
      bold: 700,        // Headings
      extrabold: 800,
      black: 900
    },

    // Line Heights
    lineHeight: {
      none: 1,
      tight: 1.25,      // Headings
      snug: 1.375,      // Subheadings
      normal: 1.5,      // Body text
      relaxed: 1.625,   // Comfortable reading
      loose: 2          // Very spacious
    },

    // Letter Spacing
    letterSpacing: {
      tighter: '-0.05em',
      tight: '-0.025em',
      normal: '0em',
      wide: '0.025em',
      wider: '0.05em',
      widest: '0.1em'
    }
  },

  // ============================================================================
  // SPACING SYSTEM
  // ============================================================================

  spacing: {
    // Base: 4px grid system
    0: '0rem',          // 0px
    px: '0.0625rem',    // 1px - Borders
    0.5: '0.125rem',    // 2px
    1: '0.25rem',       // 4px
    1.5: '0.375rem',    // 6px
    2: '0.5rem',        // 8px
    2.5: '0.625rem',    // 10px
    3: '0.75rem',       // 12px
    3.5: '0.875rem',    // 14px
    4: '1rem',          // 16px - Base unit
    5: '1.25rem',       // 20px
    6: '1.5rem',        // 24px
    7: '1.75rem',       // 28px
    8: '2rem',          // 32px
    9: '2.25rem',       // 36px
    10: '2.5rem',       // 40px
    11: '2.75rem',      // 44px
    12: '3rem',         // 48px
    14: '3.5rem',       // 56px
    16: '4rem',         // 64px
    20: '5rem',         // 80px
    24: '6rem',         // 96px
    28: '7rem',         // 112px
    32: '8rem',         // 128px
    36: '9rem',         // 144px
    40: '10rem',        // 160px
    44: '11rem',        // 176px
    48: '12rem',        // 192px
    52: '13rem',        // 208px
    56: '14rem',        // 224px
    60: '15rem',        // 240px
    64: '16rem',        // 256px
    72: '18rem',        // 288px
    80: '20rem',        // 320px
    96: '24rem'         // 384px
  },

  // ============================================================================
  // BORDER SYSTEM
  // ============================================================================

  border: {
    // Border Widths
    width: {
      0: '0',
      1: '1px',
      2: '2px',
      4: '4px',
      8: '8px'
    },

    // Border Radius
    radius: {
      none: '0',
      sm: '0.125rem',     // 2px
      base: '0.25rem',    // 4px
      md: '0.375rem',     // 6px
      lg: '0.5rem',       // 8px
      xl: '0.75rem',      // 12px
      '2xl': '1rem',      // 16px
      '3xl': '1.5rem',    // 24px
      full: '9999px'      // Circular
    }
  },

  // ============================================================================
  // SHADOW SYSTEM
  // ============================================================================

  shadows: {
    // Elevation shadows (light mode)
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',

    // Special shadows
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
    none: 'none',

    // Focus shadows (for keyboard navigation)
    focusRing: '0 0 0 3px rgba(99, 102, 241, 0.5)',
    focusRingError: '0 0 0 3px rgba(239, 68, 68, 0.5)',
    focusRingSuccess: '0 0 0 3px rgba(34, 197, 94, 0.5)'
  },

  // ============================================================================
  // ANIMATION SYSTEM
  // ============================================================================

  animation: {
    // Duration
    duration: {
      instant: '0ms',
      fast: '150ms',
      normal: '200ms',
      slow: '300ms',
      slower: '500ms',
      slowest: '700ms'
    },

    // Easing functions
    easing: {
      linear: 'linear',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',

      // Custom enterprise easing
      smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
    },

    // Transition presets
    transition: {
      all: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
      colors: 'color 200ms cubic-bezier(0.4, 0, 0.2, 1), background-color 200ms cubic-bezier(0.4, 0, 0.2, 1), border-color 200ms cubic-bezier(0.4, 0, 0.2, 1)',
      opacity: 'opacity 200ms cubic-bezier(0.4, 0, 0.2, 1)',
      transform: 'transform 200ms cubic-bezier(0.4, 0, 0.2, 1)',
      shadow: 'box-shadow 200ms cubic-bezier(0.4, 0, 0.2, 1)'
    }
  },

  // ============================================================================
  // Z-INDEX SYSTEM
  // ============================================================================

  zIndex: {
    base: 0,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    backdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
    notification: 1080,
    max: 9999
  },

  // ============================================================================
  // BREAKPOINTS
  // ============================================================================

  breakpoints: {
    sm: '640px',      // Small devices (landscape phones)
    md: '768px',      // Medium devices (tablets)
    lg: '1024px',     // Large devices (laptops)
    xl: '1280px',     // Extra large devices (desktops)
    '2xl': '1536px'   // 2X large devices (large desktops)
  },

  // ============================================================================
  // LAYOUT CONSTRAINTS
  // ============================================================================

  layout: {
    // Container max widths
    container: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
      full: '100%'
    },

    // Content max widths (for readability)
    maxWidth: {
      prose: '65ch',      // ~650px at base font size
      narrow: '45rem',    // 720px
      normal: '60rem',    // 960px
      wide: '80rem',      // 1280px
      full: '100%'
    }
  },

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================

  accessibility: {
    // Minimum touch/click targets
    minTouchTarget: {
      ios: '44px',
      android: '48px',
      web: '44px'
    },

    // Focus indicators
    focusVisible: {
      outline: '2px solid',
      outlineOffset: '2px',
      outlineColor: '#6366F1'
    },

    // Motion preferences
    reducedMotion: {
      transition: 'none',
      animation: 'none'
    }
  }
};

// Export individual token categories for convenience
export const { colors, typography, spacing, border, shadows, animation, zIndex, breakpoints, layout, accessibility } = tokens;

// Default export
export default tokens;
