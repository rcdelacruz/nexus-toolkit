"use client"

import { useSession, signOut } from "next-auth/react"
import { Button } from "@/components/ui/button"

export function TopBar() {
  const { data: session } = useSession()

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-6">
      <div />
      <div className="flex items-center gap-4">
        {session?.user?.name && (
          <span className="text-sm text-muted-foreground">{session.user.name}</span>
        )}
        <Button variant="ghost" size="sm" onClick={() => signOut()}>
          Sign out
        </Button>
      </div>
    </header>
  )
}
