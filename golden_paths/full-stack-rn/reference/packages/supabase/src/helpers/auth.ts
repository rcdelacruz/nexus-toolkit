import type { SupabaseClient } from "@supabase/supabase-js"
import type { Database } from "../types/database.js"

type TypedSupabaseClient = SupabaseClient<Database>

export async function signInWithEmail(
  supabase: TypedSupabaseClient,
  email: string,
  password: string,
) {
  return supabase.auth.signInWithPassword({ email, password })
}

export async function signInWithGoogle(supabase: TypedSupabaseClient, redirectTo: string) {
  return supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo },
  })
}

export async function signOut(supabase: TypedSupabaseClient) {
  return supabase.auth.signOut()
}

export async function getUser(supabase: TypedSupabaseClient) {
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser()
  if (error) return null
  return user
}

export async function getSession(supabase: TypedSupabaseClient) {
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession()
  if (error) return null
  return session
}
