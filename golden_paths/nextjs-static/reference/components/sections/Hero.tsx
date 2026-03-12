import { Button } from "@/components/ui/button"

export function Hero() {
  return (
    <section className="py-24 text-center">
      <div className="container mx-auto max-w-4xl px-4">
        <h1 className="mb-6 text-5xl font-bold tracking-tight">
          Build something{" "}
          <span className="text-primary">amazing</span>
        </h1>
        <p className="mb-10 text-xl text-muted-foreground">
          The fastest way to ship your next product.
        </p>
        <div className="flex justify-center gap-4">
          <Button size="lg">Get Started</Button>
          <Button size="lg" variant="outline">Learn More</Button>
        </div>
      </div>
    </section>
  )
}
