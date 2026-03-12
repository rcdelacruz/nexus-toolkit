import { View } from "react-native"
import { cn } from "../lib/utils"

interface CardProps {
  readonly children: React.ReactNode
  readonly className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <View className={cn("rounded-lg border border-gray-200 bg-white p-4 shadow-sm", className)}>
      {children}
    </View>
  )
}
