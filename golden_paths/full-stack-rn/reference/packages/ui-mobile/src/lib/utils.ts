import { clsx, type ClassValue } from "clsx"

/** className merger for NativeWind (clsx only — tailwind-merge not needed for RN) */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}
