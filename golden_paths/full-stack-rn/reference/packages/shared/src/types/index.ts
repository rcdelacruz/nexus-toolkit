/**
 * Shared TypeScript types — used by both apps/web and apps/mobile.
 *
 * Rules:
 * - No platform-specific imports (no React, no next/*, no expo/*)
 * - No UI concerns — pure data shapes
 * - Export everything from this barrel; apps import by name
 */

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface User {
  readonly id: string
  readonly email: string
  readonly displayName: string | null
  readonly avatarUrl: string | null
  readonly role: UserRole
  readonly createdAt: string
}

export type UserRole = "admin" | "member" | "viewer"

// ─── API Responses ────────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  readonly data: T
  readonly error: null
}

export interface ApiError {
  readonly data: null
  readonly error: {
    readonly code: string
    readonly message: string
  }
}

export type ApiResult<T> = ApiResponse<T> | ApiError

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  readonly items: readonly T[]
  readonly total: number
  readonly page: number
  readonly pageSize: number
  readonly hasMore: boolean
}

export interface PaginationParams {
  readonly page?: number
  readonly pageSize?: number
}
