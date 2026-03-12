import { createCallerFactory, createTRPCRouter } from "@/server/trpc"
import { exampleRouter } from "@/server/api/routers/example"

/**
 * Primary router for the server.
 * Add sub-routers here.
 */
export const appRouter = createTRPCRouter({
  example: exampleRouter,
});

export type AppRouter = typeof appRouter;

export const createCaller = createCallerFactory(appRouter);
