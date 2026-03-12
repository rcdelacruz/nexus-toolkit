import { Link } from "react-router"
import { buttonVariants } from "@/components/ui/button"

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-6xl font-bold">404</h1>
      <p className="text-muted-foreground">Page not found.</p>
      <Link to="/" className={buttonVariants()}>Go home</Link>
    </div>
  )
}
