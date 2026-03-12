/**
 * CSRF origin validation for API route handlers.
 *
 * Next.js Server Actions have built-in CSRF protection via cryptographic tokens.
 * This helper is for custom `route.ts` handlers that accept state-mutating requests
 * (POST / PUT / PATCH / DELETE).
 *
 * Usage:
 *   import { validateCsrfOrigin } from "@/lib/csrf"
 *
 *   export async function POST(req: Request) {
 *     if (!validateCsrfOrigin(req)) {
 *       return Response.json({ error: "Forbidden" }, { status: 403 })
 *     }
 *     // ...handle the request
 *   }
 */

const allowedOrigins = new Set<string>([
  process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
  ...(process.env.NODE_ENV === "development"
    ? ["http://localhost:3000", "http://localhost:3001"]
    : []),
])

/**
 * Returns true if the request Origin header matches an allowed origin.
 * Call at the top of POST / PUT / PATCH / DELETE route handlers.
 */
export function validateCsrfOrigin(req: Request): boolean {
  const origin = req.headers.get("origin")

  // No Origin header — likely a same-origin or server-to-server request.
  // Allow if a Host header is present (direct API call without browser origin).
  if (!origin) {
    return req.headers.get("host") !== null
  }

  try {
    return allowedOrigins.has(new URL(origin).origin)
  } catch {
    return false
  }
}
