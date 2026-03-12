/**
 * Auth Middleware (proxy.ts)
 *
 * Runs on the Next.js Edge runtime before every matched request.
 * Use this file to enforce authentication and route-level authorization
 * across your entire application in one place.
 *
 * ── HOW TO ENABLE ──────────────────────────────────────────────────────────
 *
 * 1. Configure apps/web/lib/auth.ts with your NextAuth v5 / Auth.js provider(s)
 * 2. Replace the placeholder export at the bottom with the implementation below
 * 3. Adjust `publicRoutes` to match your app's public pages
 * 4. Adjust `matcher` to exclude static assets and auth API routes
 *
 * ── EXAMPLE IMPLEMENTATION ─────────────────────────────────────────────────
 *
 * import { auth } from "@/lib/auth"
 *
 * const publicRoutes = ["/", "/login", "/register"]
 *
 * export default auth((req) => {
 *   const isLoggedIn = !!req.auth
 *   const isPublic = publicRoutes.some((route) =>
 *     req.nextUrl.pathname.startsWith(route)
 *   )
 *   if (!isPublic && !isLoggedIn) {
 *     return Response.redirect(new URL("/login", req.nextUrl))
 *   }
 *   // Redirect authenticated users away from auth pages
 *   const isAuthPage = ["/login", "/register"].some((r) =>
 *     req.nextUrl.pathname.startsWith(r)
 *   )
 *   if (isAuthPage && isLoggedIn) {
 *     return Response.redirect(new URL("/dashboard", req.nextUrl))
 *   }
 * })
 *
 * export const config = {
 *   matcher: [
 *     // Skip Next.js internals, static files, and auth API routes
 *     "/((?!_next/static|_next/image|favicon.ico|api/auth|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
 *   ],
 * }
 *
 * ── PLACEHOLDER ────────────────────────────────────────────────────────────
 * Remove this export once auth middleware is configured above.
 */
export function middleware() {}
export const config: { matcher: string[] } = { matcher: [] }
