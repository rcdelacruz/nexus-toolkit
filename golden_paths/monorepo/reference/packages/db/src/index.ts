import { PrismaClient } from "./generated/client"
import { PrismaPg } from "@prisma/adapter-pg"
import { Pool } from "pg"

const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  // For cloud databases with built-in poolers (Supabase port 6543, Neon PgBouncer):
  // set DB_POOL_MAX=1 to avoid double-pooling.
  // For Neon serverless/edge deployments, swap to @prisma/adapter-neon instead.
  max: parseInt(process.env.DB_POOL_MAX ?? "10"),
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 2_000,
})

const globalForPrisma = globalThis as unknown as { db: PrismaClient }

export const db =
  globalForPrisma.db ??
  new PrismaClient({
    adapter: new PrismaPg(pool),
    log: process.env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"],
  })

if (process.env.NODE_ENV !== "production") globalForPrisma.db = db

export * from "./generated/client"
