import { redirect } from "next/navigation"
import { cookies } from "next/headers"
import { createSupabaseServerClient } from "@project-name/supabase"

interface DashboardLayoutProps {
  readonly children: React.ReactNode
}

export default async function DashboardLayout({ children }: DashboardLayoutProps) {
  const supabase = createSupabaseServerClient(await cookies())
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="w-64 border-r border-border bg-card px-4 py-6">
        <nav className="space-y-1">
          <p className="mb-4 text-sm font-semibold text-foreground">Navigation</p>
          <a
            href="/dashboard"
            className="flex items-center rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent"
          >
            Dashboard
          </a>
        </nav>
      </aside>
      <main className="flex-1 px-6 py-8">{children}</main>
    </div>
  )
}
