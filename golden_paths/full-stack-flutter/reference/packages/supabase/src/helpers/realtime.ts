import type { RealtimeChannel, SupabaseClient } from "@supabase/supabase-js"
import type { Database } from "../types/database.js"

type TypedSupabaseClient = SupabaseClient<Database>
type TableName = keyof Database["public"]["Tables"]

/**
 * Subscribe to real-time INSERT/UPDATE/DELETE events on a Supabase table.
 * Returns the channel for manual cleanup via unsubscribeFromTable().
 */
export function subscribeToTable<T extends TableName>(
  supabase: TypedSupabaseClient,
  table: T,
  callback: (payload: {
    eventType: "INSERT" | "UPDATE" | "DELETE"
    new: Database["public"]["Tables"][T]["Row"] | null
    old: Database["public"]["Tables"][T]["Row"] | null
  }) => void,
): RealtimeChannel {
  return supabase
    .channel(`table-changes:${table}`)
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table },
      (payload) => {
        callback({
          eventType: payload.eventType as "INSERT" | "UPDATE" | "DELETE",
          new: (payload.new ?? null) as Database["public"]["Tables"][T]["Row"] | null,
          old: (payload.old ?? null) as Database["public"]["Tables"][T]["Row"] | null,
        })
      },
    )
    .subscribe()
}

export async function unsubscribeFromTable(channel: RealtimeChannel): Promise<void> {
  await channel.unsubscribe()
}
