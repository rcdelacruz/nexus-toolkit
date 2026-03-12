/**
 * Auto-generated Supabase database types.
 * Regenerate by running: supabase gen types typescript --local > packages/supabase/src/types/database.ts
 *
 * This placeholder covers the tables defined in sql/schema.sql.
 * Replace with real generated types after applying your schema.
 */

export interface Database {
  public: {
    Tables: {
      user_roles: {
        Row: {
          id: string
          user_id: string
          role: "admin" | "member" | "viewer"
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          role?: "admin" | "member" | "viewer"
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          role?: "admin" | "member" | "viewer"
          created_at?: string
          updated_at?: string
        }
      }
      audit_logs: {
        Row: {
          id: string
          user_id: string | null
          action: string
          resource: string
          resource_id: string | null
          metadata: Record<string, unknown> | null
          ip_address: string | null
          created_at: string
        }
        Insert: {
          id?: string
          user_id?: string | null
          action: string
          resource: string
          resource_id?: string | null
          metadata?: Record<string, unknown> | null
          ip_address?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string | null
          action?: string
          resource?: string
          resource_id?: string | null
          metadata?: Record<string, unknown> | null
          ip_address?: string | null
          created_at?: string
        }
      }
    }
    Views: Record<string, never>
    Functions: Record<string, never>
    Enums: {
      user_role: "admin" | "member" | "viewer"
    }
  }
}
