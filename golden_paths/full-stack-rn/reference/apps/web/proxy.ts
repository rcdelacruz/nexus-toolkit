/**
 * Auth Middleware (proxy.ts)
 *
 * Runs on the Next.js Edge runtime before every matched request.
 * Use this file to enforce authentication and route-level authorization
 * across your entire application in one place.
 *
 * ── HOW TO ENABLE ──────────────────────────────────────────────────────────
 *
 * 1. Install the Supabase SSR package: pnpm add @supabase/ssr
 * 2. Replace the placeholder export at the bottom with the implementation below
 * 3. Adjust `PROTECTED_PREFIXES` and `AUTH_PATHS` to match your app's routes
 * 4. Adjust `matcher` to exclude static assets
 *
 * ── EXAMPLE IMPLEMENTATION ─────────────────────────────────────────────────
 *
 * import { createServerClient } from "@supabase/ssr"
 * import { type NextRequest, NextResponse } from "next/server"
 *
 * const PROTECTED_PREFIXES = ["/dashboard"]
 * const AUTH_PATHS = ["/login", "/signup"]
 *
 * export async function middleware(request: NextRequest) {
 *   let supabaseResponse = NextResponse.next({ request })
 *
 *   const supabase = createServerClient(
 *     process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
 *     process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
 *     {
 *       cookies: {
 *         getAll() { return request.cookies.getAll() },
 *         setAll(cookiesToSet) {
 *           cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
 *           supabaseResponse = NextResponse.next({ request })
 *           cookiesToSet.forEach(({ name, value, options }) =>
 *             supabaseResponse.cookies.set(name, value, options)
 *           )
 *         },
 *       },
 *     }
 *   )
 *
 *   const { data: { user } } = await supabase.auth.getUser()
 *   const { pathname } = request.nextUrl
 *   const isProtected = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p))
 *   const isAuthPath = AUTH_PATHS.some((p) => pathname.startsWith(p))
 *
 *   if (isProtected && !user) {
 *     const url = request.nextUrl.clone()
 *     url.pathname = "/login"
 *     return NextResponse.redirect(url)
 *   }
 *   if (isAuthPath && user) {
 *     const url = request.nextUrl.clone()
 *     url.pathname = "/dashboard"
 *     return NextResponse.redirect(url)
 *   }
 *
 *   return supabaseResponse
 * }
 *
 * export const config = {
 *   matcher: [
 *     "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
 *   ],
 * }
 *
 * ── PLACEHOLDER ────────────────────────────────────────────────────────────
 * Remove this export once auth middleware is configured above.
 */
export function middleware() {}
export const config: { matcher: string[] } = { matcher: [] }
