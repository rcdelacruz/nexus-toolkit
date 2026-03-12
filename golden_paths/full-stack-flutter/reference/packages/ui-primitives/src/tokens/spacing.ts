/**
 * Spacing design tokens — 4px base unit scale.
 *
 * Keys map directly to Tailwind's numeric scale (1 = 4px, 2 = 8px, etc.)
 * Use these values for React Native StyleSheet padding/margin,
 * or reference the equivalent Tailwind class on web/mobile.
 *
 * Example:
 *   spacingTokens[4]  → 16  (px)  → className="p-4"
 *   spacingTokens[8]  → 32  (px)  → className="p-8"
 */

export const spacingTokens = {
  0: 0,
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  2.5: 10,
  3: 12,
  3.5: 14,
  4: 16,
  5: 20,
  6: 24,
  7: 28,
  8: 32,
  9: 36,
  10: 40,
  11: 44,
  12: 48,
  14: 56,
  16: 64,
  20: 80,
  24: 96,
  28: 112,
  32: 128,
  36: 144,
  40: 160,
  48: 192,
  56: 224,
  64: 256,
} as const

export type SpacingScale = keyof typeof spacingTokens
export type SpacingTokens = typeof spacingTokens
