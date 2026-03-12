export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const shutdown = (signal: string) => {
      console.log(`${signal} received, shutting down gracefully...`)
      process.exit(0)
    }
    process.once("SIGTERM", () => shutdown("SIGTERM"))
    process.once("SIGINT", () => shutdown("SIGINT"))
  }
}
