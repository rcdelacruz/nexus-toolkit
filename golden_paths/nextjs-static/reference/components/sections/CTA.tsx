import { Button } from "@/components/ui/button"

export function CTA() {
  return (
    <section className="py-24 bg-primary text-primary-foreground">
      <div className="container mx-auto px-4 text-center">
        <h2 className="mb-4 text-4xl font-bold">Ready to get started?</h2>
        <p className="mb-8 text-lg opacity-90">Join thousands of teams shipping faster.</p>
        <Button size="lg" variant="secondary">Start for free</Button>
      </div>
    </section>
  )
}
