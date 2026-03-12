import { Pressable, Text } from "react-native"
import { cn } from "../lib/utils"

interface ButtonProps {
  readonly children: React.ReactNode
  readonly onPress?: () => void
  readonly className?: string
  readonly disabled?: boolean
  readonly variant?: "default" | "outline" | "ghost"
}

export function Button({
  children,
  onPress,
  className,
  disabled,
  variant = "default",
}: ButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      className={cn(
        "flex-row items-center justify-center rounded-md px-4 py-2",
        variant === "default" && "bg-blue-600",
        variant === "outline" && "border border-blue-600 bg-transparent",
        variant === "ghost" && "bg-transparent",
        disabled && "opacity-50",
        className,
      )}
    >
      <Text
        className={cn(
          "text-sm font-medium",
          variant === "default" && "text-white",
          variant === "outline" && "text-blue-600",
          variant === "ghost" && "text-blue-600",
        )}
      >
        {children}
      </Text>
    </Pressable>
  )
}
