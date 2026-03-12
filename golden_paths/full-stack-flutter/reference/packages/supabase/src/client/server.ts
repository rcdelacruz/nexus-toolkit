import { createServerClient, type CookieMethods } from "@supabase/ssr"
import type { Database } from "../types/database.js"

/**
 * Creates a Supabase client for use in Next.js Server Components and Route Handlers.
 * The `cookies` parameter must be provided from `next/headers`.
 *
 * @example
 * import { cookies } from "next/headers"
 * const supabase = createSupabaseServerClient(await cookies())
 */
export function createSupabaseServerClient(cookieStore: CookieMethods) {
  return createServerClient<Database>(
    process.env["NEXT_PUBLIC_SUPABASE_URL"] ?? "",
    process.env["NEXT_PUBLIC_SUPABASE_ANON_KEY"] ?? "",
    { cookies: cookieStore },
  )
}

/**
 * Creates a Supabase admin client using the service role key.
 * NEVER expose this in client components or mobile apps.
 * Use only in trusted server contexts (Route Handlers, cron jobs).
 */
export function createSupabaseAdminClient() {
  return createServerClient<Database>(
    process.env["NEXT_PUBLIC_SUPABASE_URL"] ?? "",
    process.env["SUPABASE_SERVICE_ROLE_KEY"] ?? "",
    {
      cookies: {
        getAll: () => [],
        setAll: () => undefined,
      },
    },
  )
}
