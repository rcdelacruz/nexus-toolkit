/**
 * Color design tokens — source of truth for all brand and semantic colors.
 *
 * These are platform-agnostic JS constants. They are consumed by:
 *   - packages/ui-web/src/styles/globals.css  (mapped to CSS custom properties)
 *   - packages/ui-mobile components            (used directly as className values or inline)
 *
 * When Figma Make exports a design system, replace these values with the
 * extracted tokens from the Figma file. All colors must be expressible as
 * HSL so the web layer can emit hsl() CSS variables.
 */

export const colorTokens = {
  /** Brand palette */
  brand: {
    primary: "#3b82f6",       // hsl(221 83% 53%)
    primaryForeground: "#f8fafc", // hsl(210 40% 98%)
    secondary: "#64748b",     // hsl(215 16% 47%)
    secondaryForeground: "#f8fafc",
    accent: "#f1f5f9",        // hsl(210 40% 96%)
    accentForeground: "#1e293b",
  },

  /** Semantic / surface palette */
  semantic: {
    background: "#ffffff",    // hsl(0 0% 100%)
    foreground: "#0a0a0a",    // hsl(0 0% 4%)
    card: "#ffffff",
    cardForeground: "#0a0a0a",
    muted: "#f1f5f9",         // hsl(210 40% 96%)
    mutedForeground: "#64748b",
    border: "#e2e8f0",        // hsl(214 32% 91%)
    input: "#e2e8f0",
    ring: "#3b82f6",
    destructive: "#ef4444",   // hsl(0 84% 60%)
    destructiveForeground: "#f8fafc",
  },

  /** Dark mode overrides */
  dark: {
    background: "#0f172a",    // hsl(222 84% 5%)
    foreground: "#f8fafc",
    card: "#0f172a",
    cardForeground: "#f8fafc",
    muted: "#1e293b",         // hsl(217 33% 18%)
    mutedForeground: "#94a3b8",
    border: "#1e293b",
    input: "#1e293b",
    ring: "#60a5fa",
    primary: "#60a5fa",       // hsl(217 91% 60%)
    primaryForeground: "#1e293b",
  },

  /** Status colors */
  status: {
    success: "#22c55e",
    warning: "#f59e0b",
    error: "#ef4444",
    info: "#3b82f6",
  },
} as const

export type ColorTokens = typeof colorTokens
