import type { SupabaseClient } from "@supabase/supabase-js"
import type { Database } from "../types/database.js"

type TypedSupabaseClient = SupabaseClient<Database>

export async function uploadFile(
  supabase: TypedSupabaseClient,
  bucket: string,
  path: string,
  file: File | Blob | ArrayBuffer,
  options?: { contentType?: string; upsert?: boolean },
) {
  return supabase.storage.from(bucket).upload(path, file, {
    contentType: options?.contentType,
    upsert: options?.upsert ?? false,
  })
}

export function getPublicUrl(
  supabase: TypedSupabaseClient,
  bucket: string,
  path: string,
): string {
  const { data } = supabase.storage.from(bucket).getPublicUrl(path)
  return data.publicUrl
}

export async function deleteFile(
  supabase: TypedSupabaseClient,
  bucket: string,
  paths: string[],
) {
  return supabase.storage.from(bucket).remove(paths)
}
