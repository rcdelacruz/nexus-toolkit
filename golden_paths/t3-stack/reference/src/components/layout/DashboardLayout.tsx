"use client"

import { useAppStore } from "@/store/useAppStore"
import { Sidebar } from "./Sidebar"
import { TopBar } from "./TopBar"
import { cn } from "@/lib/utils"

interface DashboardLayoutProps {
  children: React.ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className={cn("flex flex-1 flex-col transition-all duration-300", sidebarOpen ? "ml-64" : "ml-16")}>
        <TopBar />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
