/**
 * Shared constants — platform-agnostic.
 *
 * Rules:
 * - No platform-specific values (no window, no Dimensions)
 * - Pure data — no functions
 */

export const USER_ROLES = {
  ADMIN: "admin",
  MEMBER: "member",
  VIEWER: "viewer",
} as const

export const PAGINATION_DEFAULTS = {
  PAGE: 1,
  PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const

export const API_ROUTES = {
  HEALTH: "/api/v1/health",
} as const
