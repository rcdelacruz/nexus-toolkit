import { createClient } from "@supabase/supabase-js"
import type { Database } from "../types/database.js"

/**
 * Creates a Supabase client for use in React Native (Expo) apps.
 * Session is persisted using expo-secure-store via a custom storage adapter.
 *
 * The ExpoSecureStoreAdapter must be provided from the mobile app
 * to avoid a hard dependency on expo-secure-store in this package.
 *
 * @example
 * import * as SecureStore from "expo-secure-store"
 * const supabase = createSupabaseMobileClient({
 *   getItem: (key) => SecureStore.getItemAsync(key),
 *   setItem: (key, value) => SecureStore.setItemAsync(key, value),
 *   removeItem: (key) => SecureStore.deleteItemAsync(key),
 * })
 */
export function createSupabaseMobileClient(storage: {
  getItem: (key: string) => Promise<string | null>
  setItem: (key: string, value: string) => Promise<void>
  removeItem: (key: string) => Promise<void>
}) {
  return createClient<Database>(
    process.env["EXPO_PUBLIC_SUPABASE_URL"] ?? "",
    process.env["EXPO_PUBLIC_SUPABASE_ANON_KEY"] ?? "",
    {
      auth: {
        storage,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
      },
    },
  )
}
