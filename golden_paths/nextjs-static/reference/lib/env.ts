import { z } from "zod"

const clientSchema = z.object({
  NEXT_PUBLIC_APP_URL: z.string().url("NEXT_PUBLIC_APP_URL must be a valid URL").optional(),
  NEXT_PUBLIC_SITE_NAME: z.string().optional(),
})

function validateEnv() {
  const parsed = clientSchema.safeParse(process.env)
  if (!parsed.success) {
    const issues = parsed.error.issues
      .map((i) => `  ${i.path.join(".")}: ${i.message}`)
      .join("\n")
    throw new Error(`Invalid environment variables:\n${issues}`)
  }
  return parsed.data
}

export const env =
  process.env.SKIP_ENV_VALIDATION !== "1"
    ? validateEnv()
    : (process.env as unknown as z.infer<typeof clientSchema>)
