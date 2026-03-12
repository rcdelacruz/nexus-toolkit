import type { SupabaseClient } from "@supabase/supabase-js"
import type { Database } from "../types/database.js"

type TypedSupabaseClient = SupabaseClient<Database>

interface AuditEventParams {
  readonly userId: string | null
  readonly action: string
  readonly resource: string
  readonly resourceId?: string | null
  readonly metadata?: Record<string, unknown> | null
  readonly ipAddress?: string | null
}

export async function logAuditEvent(
  supabase: TypedSupabaseClient,
  params: AuditEventParams,
): Promise<void> {
  const { error } = await supabase.from("audit_logs").insert({
    user_id: params.userId,
    action: params.action,
    resource: params.resource,
    resource_id: params.resourceId ?? null,
    metadata: params.metadata ?? null,
    ip_address: params.ipAddress ?? null,
  })

  if (error) {
    console.error("[audit] Failed to log audit event:", error.message)
  }
}
