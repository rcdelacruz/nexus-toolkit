import { TextInput, type TextInputProps } from "react-native"
import { cn } from "../lib/utils"

interface InputProps extends TextInputProps {
  readonly className?: string
}

export function Input({ className, ...props }: InputProps) {
  return (
    <TextInput
      className={cn(
        "h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 disabled:opacity-50",
        className,
      )}
      {...props}
    />
  )
}
