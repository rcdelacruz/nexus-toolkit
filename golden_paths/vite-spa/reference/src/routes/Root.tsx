import { Outlet } from "react-router"
import { Header } from "@/components/layout/Header"

export function Root() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <Outlet />
      </main>
    </div>
  )
}
