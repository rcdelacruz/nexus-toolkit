import { z } from "zod"

const envSchema = z.object({
  VITE_API_URL: z.string().url("VITE_API_URL must be a valid URL").optional(),
  VITE_APP_NAME: z.string().optional(),
})

function validateEnv() {
  const parsed = envSchema.safeParse(import.meta.env)
  if (!parsed.success) {
    const issues = parsed.error.issues
      .map((i) => `  ${i.path.join(".")}: ${i.message}`)
      .join("\n")
    throw new Error(`Invalid environment variables:\n${issues}`)
  }
  return parsed.data
}

export const env = import.meta.env.SKIP_ENV_VALIDATION !== "1" ? validateEnv() : import.meta.env
