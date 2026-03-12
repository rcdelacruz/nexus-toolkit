import { api, HydrateClient } from "@/trpc/server"

export default async function DashboardPage() {
  return (
    <HydrateClient>
      <div>
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        {/* Dashboard content */}
      </div>
    </HydrateClient>
  )
}
