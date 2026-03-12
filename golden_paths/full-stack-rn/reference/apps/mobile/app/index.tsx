import { useEffect } from "react"
import { View, ActivityIndicator } from "react-native"
import { router } from "expo-router"
import * as SecureStore from "expo-secure-store"
import { createSupabaseMobileClient } from "@project-name/supabase"

const supabase = createSupabaseMobileClient({
  getItem: (key) => SecureStore.getItemAsync(key),
  setItem: (key, value) => SecureStore.setItemAsync(key, value),
  removeItem: (key) => SecureStore.deleteItemAsync(key),
})

export default function IndexScreen() {
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        router.replace("/(tabs)")
      } else {
        router.replace("/(auth)/login")
      }
    })
  }, [])

  return (
    <View className="flex-1 items-center justify-center bg-white">
      <ActivityIndicator size="large" color="#3b82f6" />
    </View>
  )
}
