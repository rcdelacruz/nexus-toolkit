import { createCallerFactory, createTRPCRouter } from "@/server/trpc"
import { exampleRouter } from "@/server/api/routers/example"

export const appRouter = createTRPCRouter({
  example: exampleRouter,
})

export type AppRouter = typeof appRouter

export const createCaller = createCallerFactory(appRouter)
