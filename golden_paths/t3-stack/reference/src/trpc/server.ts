import "server-only"

import { createHydrationHelpers } from "@trpc/react-query/rsc"
import { headers } from "next/headers"
import { cache } from "react"
import { createCallerFactory, createTRPCContext } from "@/server/trpc"
import { appRouter } from "@/server/api/root"
import { makeQueryClient } from "@/trpc/query-client"

// Avoid creating a new query client for every server component
const getQueryClient = cache(makeQueryClient)

const caller = createCallerFactory(appRouter)(async () =>
  createTRPCContext({ headers: await headers() }),
)

export const { trpc: api, HydrateClient } = createHydrationHelpers<typeof appRouter>(
  caller,
  getQueryClient,
)
