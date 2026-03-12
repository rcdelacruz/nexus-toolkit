/**
 * Session middleware helper for Next.js.
 *
 * The updateSession pattern is intentionally inlined in apps/web/proxy.ts
 * because it depends on Next.js-specific types (NextRequest, NextResponse).
 *
 * Keeping it in a shared package would require `next` as a dependency of
 * @project-name/supabase, breaking the isomorphic contract with apps/mobile.
 *
 * See: apps/web/proxy.ts for the full implementation.
 */
export {}
