import { Link } from "react-router"

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      <div className="container mx-auto flex h-14 items-center justify-between px-4">
        <Link to="/" className="font-bold text-foreground">
          __PROJECT_NAME__
        </Link>
        <nav className="flex items-center gap-4" />
      </div>
    </header>
  )
}
