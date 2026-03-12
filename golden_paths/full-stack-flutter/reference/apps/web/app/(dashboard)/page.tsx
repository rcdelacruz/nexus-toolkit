import { cookies } from "next/headers"
import { createSupabaseServerClient } from "@project-name/supabase"

export default async function DashboardPage() {
  const supabase = createSupabaseServerClient(await cookies())
  const {
    data: { user },
  } = await supabase.auth.getUser()

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">Dashboard</h1>
      <p className="text-sm text-muted-foreground">
        Welcome back, {user?.email ?? "user"}.
      </p>
    </div>
  )
}
