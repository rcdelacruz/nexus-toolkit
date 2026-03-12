import { View, Text, Alert } from "react-native"
import { router } from "expo-router"
import * as SecureStore from "expo-secure-store"
import { createSupabaseMobileClient } from "@project-name/supabase"
import { Button } from "@project-name/ui-mobile"

const supabase = createSupabaseMobileClient({
  getItem: (key) => SecureStore.getItemAsync(key),
  setItem: (key, value) => SecureStore.setItemAsync(key, value),
  removeItem: (key) => SecureStore.deleteItemAsync(key),
})

export default function ProfileScreen() {
  async function handleSignOut() {
    const { error } = await supabase.auth.signOut()
    if (error) {
      Alert.alert("Sign out failed", error.message)
      return
    }
    router.replace("/(auth)/login")
  }

  return (
    <View className="flex-1 bg-white px-4 py-8">
      <Text className="mb-6 text-2xl font-bold text-gray-900">Profile</Text>
      <Button variant="outline" onPress={handleSignOut}>
        Sign out
      </Button>
    </View>
  )
}
