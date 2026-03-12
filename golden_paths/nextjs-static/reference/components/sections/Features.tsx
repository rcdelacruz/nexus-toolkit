import { Zap, Shield, Rocket } from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

const features = [
  { icon: Zap, title: "Lightning Fast", description: "Built with performance in mind." },
  { icon: Shield, title: "Secure by Default", description: "Best-in-class security practices baked in." },
  { icon: Rocket, title: "Easy to Deploy", description: "Ship to production in minutes, not days." },
]

export function Features() {
  return (
    <section id="features" className="py-24 bg-muted/50">
      <div className="container mx-auto px-4">
        <h2 className="mb-12 text-center text-3xl font-bold">Everything you need</h2>
        <div className="grid gap-8 md:grid-cols-3">
          {features.map(({ icon: Icon, title, description }) => (
            <Card key={title}>
              <CardHeader>
                <Icon className="mb-4 h-8 w-8 text-primary" />
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
