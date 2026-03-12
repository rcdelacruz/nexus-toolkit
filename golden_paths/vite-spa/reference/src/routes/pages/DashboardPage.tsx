import { useQuery } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api"

export function DashboardPage() {
  const { isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => fetchApi<{ stats: unknown[] }>("/dashboard"),
  })

  if (isLoading) return <div className="p-6">Loading...</div>

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      {/* dashboard content */}
    </div>
  )
}
