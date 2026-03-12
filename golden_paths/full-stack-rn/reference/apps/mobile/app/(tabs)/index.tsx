import { useEffect, useState } from "react"
import { View, Text, ScrollView } from "react-native"
import { Card } from "@project-name/ui-mobile"

interface HealthResponse {
  status: string
  timestamp: string
}

export default function HomeScreen() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const apiUrl = process.env["EXPO_PUBLIC_API_URL"] ?? ""
    fetch(`${apiUrl}/api/v1/health`)
      .then((res) => res.json() as Promise<HealthResponse>)
      .then(setHealth)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to reach API")
      })
  }, [])

  return (
    <ScrollView className="flex-1 bg-white">
      <View className="px-4 py-8">
        <Text className="mb-6 text-2xl font-bold text-gray-900">Home</Text>

        <Card className="mb-4">
          <Text className="mb-2 text-sm font-semibold text-gray-700">API Health Check</Text>
          {health ? (
            <>
              <Text className="text-sm text-green-600">Status: {health.status}</Text>
              <Text className="mt-1 text-xs text-gray-400">{health.timestamp}</Text>
            </>
          ) : error ? (
            <Text className="text-sm text-red-600">Error: {error}</Text>
          ) : (
            <Text className="text-sm text-gray-400">Checking…</Text>
          )}
        </Card>
      </View>
    </ScrollView>
  )
}
