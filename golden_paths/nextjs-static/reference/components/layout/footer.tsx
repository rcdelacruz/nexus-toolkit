export function Footer() {
  return (
    <footer className="border-t border-border py-8">
      <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
        <p>© {new Date().getFullYear()} __PROJECT_TITLE__. All rights reserved.</p>
      </div>
    </footer>
  )
}
