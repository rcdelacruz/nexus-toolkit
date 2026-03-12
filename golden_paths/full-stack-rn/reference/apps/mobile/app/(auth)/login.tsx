import { useState } from "react"
import { View, Text, Alert } from "react-native"
import { router } from "expo-router"
import * as SecureStore from "expo-secure-store"
import * as WebBrowser from "expo-web-browser"
import { createSupabaseMobileClient } from "@project-name/supabase"
import { Button, Input } from "@project-name/ui-mobile"

WebBrowser.maybeCompleteAuthSession()

const supabase = createSupabaseMobileClient({
  getItem: (key) => SecureStore.getItemAsync(key),
  setItem: (key, value) => SecureStore.setItemAsync(key, value),
  removeItem: (key) => SecureStore.deleteItemAsync(key),
})

export default function LoginScreen() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleEmailSignIn() {
    setLoading(true)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (error) {
      Alert.alert("Sign in failed", error.message)
      return
    }
    router.replace("/(tabs)")
  }

  async function handleGoogleSignIn() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${process.env["EXPO_PUBLIC_API_URL"]}/auth/callback`,
      },
    })
    if (error) Alert.alert("Google sign in failed", error.message)
  }

  return (
    <View className="flex-1 items-center justify-center bg-white px-6">
      <View className="w-full max-w-sm space-y-6">
        <View className="mb-8 items-center">
          <Text className="text-3xl font-bold text-gray-900">Sign in</Text>
          <Text className="mt-2 text-sm text-gray-500">Enter your credentials to continue</Text>
        </View>

        <View className="space-y-4">
          <Input
            placeholder="Email"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            className="mb-3"
          />
          <Input
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoComplete="current-password"
            className="mb-4"
          />

          <Button onPress={handleEmailSignIn} disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </Button>

          <View className="my-4 flex-row items-center">
            <View className="flex-1 border-t border-gray-200" />
            <Text className="mx-4 text-xs uppercase text-gray-400">or</Text>
            <View className="flex-1 border-t border-gray-200" />
          </View>

          <Button variant="outline" onPress={handleGoogleSignIn}>
            Continue with Google
          </Button>
        </View>
      </View>
    </View>
  )
}
