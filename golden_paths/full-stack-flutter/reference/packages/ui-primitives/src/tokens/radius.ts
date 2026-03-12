/**
 * Border radius design tokens (in pixels for React Native).
 * Maps to Tailwind's `rounded-*` classes on web.
 *
 * Example:
 *   radiusTokens.md → 8  (px)  → className="rounded-md"
 */

export const radiusTokens = {
  none: 0,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  "2xl": 24,
  "3xl": 32,
  full: 9999,
} as const

export type RadiusTokens = typeof radiusTokens
