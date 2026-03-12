import { redirect } from "next/navigation"
import { cookies } from "next/headers"
import { createSupabaseServerClient } from "@project-name/supabase"

export default async function RootPage() {
  const supabase = createSupabaseServerClient(await cookies())
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (user) {
    redirect("/dashboard")
  }

  redirect("/login")
}
