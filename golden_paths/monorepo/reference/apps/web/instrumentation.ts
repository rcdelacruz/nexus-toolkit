export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const shutdown = async (signal: string) => {
      console.log(`${signal} received, shutting down gracefully...`)
      const { db } = await import("@project-name/db")
      await db.$disconnect()
      process.exit(0)
    }
    process.once("SIGTERM", () => shutdown("SIGTERM"))
    process.once("SIGINT", () => shutdown("SIGINT"))
  }
}
