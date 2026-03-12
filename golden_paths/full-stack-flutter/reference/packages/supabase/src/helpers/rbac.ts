import type { SupabaseClient } from "@supabase/supabase-js"
import type { Database } from "../types/database.js"

type TypedSupabaseClient = SupabaseClient<Database>
type UserRole = Database["public"]["Enums"]["user_role"]

export const ROLES = {
  ADMIN: "admin" as const,
  MEMBER: "member" as const,
  VIEWER: "viewer" as const,
} satisfies Record<string, UserRole>

const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  admin: ["read", "write", "delete", "manage_users", "manage_roles"],
  member: ["read", "write"],
  viewer: ["read"],
}

export async function getUserRole(
  supabase: TypedSupabaseClient,
  userId: string,
): Promise<UserRole | null> {
  const { data, error } = await supabase
    .from("user_roles")
    .select("role")
    .eq("user_id", userId)
    .single()

  if (error || !data) return null
  return data.role
}

export async function hasPermission(
  supabase: TypedSupabaseClient,
  userId: string,
  action: string,
): Promise<boolean> {
  const role = await getUserRole(supabase, userId)
  if (!role) return false

  const permissions = ROLE_PERMISSIONS[role]
  return permissions.includes(action)
}
