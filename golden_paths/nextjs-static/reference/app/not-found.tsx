import Link from "next/link"

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h2 className="text-xl font-semibold">404 — Page not found</h2>
      <p className="text-muted-foreground text-sm">
        The page you are looking for does not exist.
      </p>
      <Link
        href="/"
        className="rounded-md bg-foreground px-4 py-2 text-sm text-background hover:opacity-90"
      >
        Go home
      </Link>
    </div>
  )
}
