# Golden Path Specification
> Company Frontend Boilerplate Standard — MCP Reference Document
> Version 2.0.0 — Updated February 2026

---

## Confirmed Stack (Latest & Greatest)

| Concern | Choice | Version |
|---|---|---|
| Framework | Next.js (App Router) | **^16.1** |
| Runtime | React | **^19.2** |
| Styling | Tailwind CSS | **^4.x** (CSS-first, no config file) |
| Components | shadcn/ui | **latest** (Tailwind v4 compatible) |
| State | Zustand | **^5.0** |
| Data Fetching | tRPC + TanStack Query | **^11.10 / ^5.x** |
| Auth | NextAuth v5 (Auth.js) | **^5.x beta** |
| ORM | Prisma | **^7.4** |
| Monorepo | pnpm workspaces | pnpm **^9** |
| Testing | Vitest | **^3.x** |
| CI/CD | Dockerfile + Docker Compose | — |
| TypeScript | strict: true | **^5.8** |
| Import Alias | `@/` | — |
| File Naming | PascalCase (`Button.tsx`) | — |
| Route Folders | kebab-case | — |
| Env Vars | plain `process.env` | — |
| Toasts | Sonner | **^2.x** |
| Package Manager | pnpm | **^9** |
| Git Hooks | Husky + Commitlint | **^9 / ^19** |
| SPA Router | React Router | **v7** |
| Vite (SPA) | Vite | **^6.x** |

---

## ⚠️ Breaking Changes vs Previous Stack

These are **not incremental updates** — each item below requires meaningfully different code patterns.

### Tailwind v4 — CSS-first, no more `tailwind.config.ts`
Tailwind v4 is a complete rewrite. The `tailwind.config.ts` file is **gone**. Configuration now lives entirely in your CSS file using `@theme`. The Vite plugin `@tailwindcss/vite` replaces PostCSS. `tailwindcss-animate` is **deprecated** — use `tw-animate-css` instead. Content detection is automatic — no `content` array needed.

```css
/* globals.css — THE new way */
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  /* ... rest of tokens */
}

:root {
  --background: hsl(0 0% 100%);
  --foreground: hsl(0 0% 3.9%);
  --primary: hsl(221.2 83.2% 53.3%);
  --primary-foreground: hsl(210 40% 98%);
  --secondary: hsl(210 40% 96.1%);
  --secondary-foreground: hsl(222.2 47.4% 11.2%);
  --muted: hsl(210 40% 96.1%);
  --muted-foreground: hsl(215.4 16.3% 46.9%);
  --accent: hsl(210 40% 96.1%);
  --accent-foreground: hsl(222.2 47.4% 11.2%);
  --destructive: hsl(0 84.2% 60.2%);
  --destructive-foreground: hsl(210 40% 98%);
  --border: hsl(214.3 31.8% 91.4%);
  --input: hsl(214.3 31.8% 91.4%);
  --ring: hsl(221.2 83.2% 53.3%);
  --radius: 0.5rem;
  --card: hsl(0 0% 100%);
  --card-foreground: hsl(0 0% 3.9%);
  --popover: hsl(0 0% 100%);
  --popover-foreground: hsl(0 0% 3.9%);
  --chart-1: hsl(12 76% 61%);
  --chart-2: hsl(173 58% 39%);
  --chart-3: hsl(197 37% 24%);
  --chart-4: hsl(43 74% 66%);
  --chart-5: hsl(27 87% 67%);
}

.dark {
  --background: hsl(0 0% 3.9%);
  --foreground: hsl(0 0% 98%);
  --primary: hsl(217.2 91.2% 59.8%);
  --primary-foreground: hsl(222.2 47.4% 11.2%);
  /* ... other dark tokens */
}

@layer base {
  * { @apply border-border outline-ring/50; }
  body { @apply bg-background text-foreground; }
}
```

### Next.js 16 — Async params, `proxy.ts`
`params` and `searchParams` in pages/layouts are now async. `middleware.ts` is renamed to `proxy.ts`. React Compiler is stable and can be enabled.

```tsx
// ✅ Next.js 16 — params are async
export default async function Page(props: { params: Promise<{ slug: string }> }) {
  const { slug } = await props.params
  return <h1>{slug}</h1>
}
```

### Prisma 7 — ESM, `prisma.config.ts`, new generator
Prisma now ships as an ES module. New `prisma.config.ts` config file. The `prisma-client-js` generator is replaced by `prisma-client`. **MongoDB not yet supported in v7** — stay on v6 for MongoDB projects.

```ts
// prisma.config.ts (new in v7)
import path from "node:path"
import { defineConfig } from "prisma/config"

export default defineConfig({
  earlyAccess: true,
  schema: path.join("prisma", "schema.prisma"),
})
```

### NextAuth v5 — `AUTH_` env prefix, no `NEXTAUTH_URL`
All env variables now use `AUTH_` prefix. `NEXTAUTH_SECRET` → `AUTH_SECRET`. `NEXTAUTH_URL` is auto-detected from request headers in most environments. `proxy.ts` (Next.js 16) replaces `middleware.ts` for auth protection.

### React 19.2 — No `forwardRef`
shadcn/ui components no longer use `forwardRef`. Components accept `ref` as a regular prop. Remove any manual `forwardRef` wrappers in your components.

### Zustand v5 — Stricter types
Zustand v5 removed some deprecated patterns. The `devtools`, `persist`, and `immer` middlewares all still work but types are stricter. No `set` method return type issues.

---

## Shared Standards (Apply to ALL Golden Paths)

### TypeScript Config

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### ESLint Config (Flat Config — ESLint v9)

```js
// eslint.config.mjs
import { dirname } from "path"
import { fileURLToPath } from "url"
import { FlatCompat } from "@eslint/eslintrc"
import tseslint from "typescript-eslint"

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const compat = new FlatCompat({ baseDirectory: __dirname })

export default tseslint.config(
  ...compat.extends("next/core-web-vitals"),
  ...tseslint.configs.recommendedTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: __dirname,
      },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/consistent-type-imports": [
        "warn",
        { prefer: "type-imports", fixStyle: "inline-type-imports" },
      ],
      "@typescript-eslint/no-misused-promises": [
        "error",
        { checksVoidReturn: { attributes: false } },
      ],
    },
  }
)
```

### Prettier Config

```json
// .prettierrc
{
  "semi": false,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

### Husky Setup

```bash
# .husky/pre-commit
pnpm lint-staged
```

```bash
# .husky/commit-msg
npx --no -- commitlint --edit ${1}
```

```js
// commitlint.config.mjs
export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "ci", "revert"],
    ],
    "subject-case": [2, "always", "lower-case"],
    "header-max-length": [2, "always", 100],
  },
}
```

```json
// package.json (lint-staged section)
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md,css}": ["prettier --write"]
  }
}
```

### lib/utils.ts

```ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(date)
}

export function absoluteUrl(path: string) {
  return `${process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"}${path}`
}
```

### Dockerfile

```dockerfile
FROM node:22-alpine AS base
RUN corepack enable && corepack prepare pnpm@latest --activate

FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
```

### docker-compose.yml

```yaml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - AUTH_SECRET=${AUTH_SECRET}
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

---

## Golden Path 1: Next.js Fullstack (App Router)

**Use when:** Figma Make output contains authenticated pages, dashboards, forms, or data-driven UI.

### Folder Structure

```
my-app/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   └── dashboard/
│   │       └── page.tsx
│   ├── api/
│   │   ├── auth/
│   │   │   └── [...nextauth]/
│   │   │       └── route.ts
│   │   └── trpc/
│   │       └── [trpc]/
│   │           └── route.ts
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css              ← Tailwind v4 CSS-first config lives here
├── components/
│   ├── ui/                      ← shadcn/ui components (no forwardRef)
│   └── layout/
│       ├── Header.tsx
│       ├── Footer.tsx
│       └── Sidebar.tsx
├── lib/
│   ├── utils.ts
│   ├── auth.ts
│   └── db.ts
├── server/
│   ├── api/
│   │   ├── root.ts
│   │   └── routers/
│   │       └── example.ts
│   └── trpc.ts
├── trpc/
│   ├── react.tsx
│   └── server.ts
├── store/
│   └── useAppStore.ts
├── types/
│   └── index.ts
├── hooks/
├── public/
├── prisma/
│   ├── schema.prisma
│   └── config.ts               ← Prisma v7 config file
├── proxy.ts                    ← Next.js 16: was middleware.ts
├── .env
├── .env.example
├── next.config.ts
├── tsconfig.json
├── package.json
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Reference Files

#### app/layout.tsx
```tsx
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Toaster } from "sonner"
import { TRPCReactProvider } from "@/trpc/react"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })

export const metadata: Metadata = {
  title: { default: "My App", template: "%s | My App" },
  description: "My application description",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <TRPCReactProvider>
          {children}
          <Toaster richColors position="top-right" />
        </TRPCReactProvider>
      </body>
    </html>
  )
}
```

#### app/globals.css
```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --font-sans: var(--font-inter);
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}

:root {
  --background: hsl(0 0% 100%);
  --foreground: hsl(0 0% 3.9%);
  --card: hsl(0 0% 100%);
  --card-foreground: hsl(0 0% 3.9%);
  --popover: hsl(0 0% 100%);
  --popover-foreground: hsl(0 0% 3.9%);
  --primary: hsl(221.2 83.2% 53.3%);
  --primary-foreground: hsl(210 40% 98%);
  --secondary: hsl(210 40% 96.1%);
  --secondary-foreground: hsl(222.2 47.4% 11.2%);
  --muted: hsl(210 40% 96.1%);
  --muted-foreground: hsl(215.4 16.3% 46.9%);
  --accent: hsl(210 40% 96.1%);
  --accent-foreground: hsl(222.2 47.4% 11.2%);
  --destructive: hsl(0 84.2% 60.2%);
  --destructive-foreground: hsl(210 40% 98%);
  --border: hsl(214.3 31.8% 91.4%);
  --input: hsl(214.3 31.8% 91.4%);
  --ring: hsl(221.2 83.2% 53.3%);
  --radius: 0.5rem;
}

.dark {
  --background: hsl(222.2 84% 4.9%);
  --foreground: hsl(210 40% 98%);
  --primary: hsl(217.2 91.2% 59.8%);
  --primary-foreground: hsl(222.2 47.4% 11.2%);
  --secondary: hsl(217.2 32.6% 17.5%);
  --secondary-foreground: hsl(210 40% 98%);
  --muted: hsl(217.2 32.6% 17.5%);
  --muted-foreground: hsl(215 20.2% 65.1%);
  --accent: hsl(217.2 32.6% 17.5%);
  --accent-foreground: hsl(210 40% 98%);
  --destructive: hsl(0 62.8% 30.6%);
  --destructive-foreground: hsl(210 40% 98%);
  --border: hsl(217.2 32.6% 17.5%);
  --input: hsl(217.2 32.6% 17.5%);
  --ring: hsl(224.3 76.3% 48%);
}

@layer base {
  * { @apply border-border outline-ring/50; }
  body { @apply bg-background text-foreground; }
}
```

#### next.config.ts
```ts
import type { NextConfig } from "next"

const config: NextConfig = {
  output: "standalone",
  experimental: {
    reactCompiler: true,  // React Compiler stable in Next.js 16
  },
}

export default config
```

#### proxy.ts (was middleware.ts in Next.js < 16)
```ts
import { auth } from "@/lib/auth"

export default auth((req) => {
  const isLoggedIn = !!req.auth
  const isAuthPage = req.nextUrl.pathname.startsWith("/login") ||
    req.nextUrl.pathname.startsWith("/register")
  const isDashboard = req.nextUrl.pathname.startsWith("/dashboard")

  if (isDashboard && !isLoggedIn) {
    return Response.redirect(new URL("/login", req.nextUrl))
  }
  if (isAuthPage && isLoggedIn) {
    return Response.redirect(new URL("/dashboard", req.nextUrl))
  }
})

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}
```

#### lib/auth.ts
```ts
import NextAuth from "next-auth"
import { PrismaAdapter } from "@auth/prisma-adapter"
import GitHub from "next-auth/providers/github"
import Google from "next-auth/providers/google"
import { db } from "@/lib/db"

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(db),
  providers: [
    GitHub,   // Auto-reads AUTH_GITHUB_ID and AUTH_GITHUB_SECRET
    Google,   // Auto-reads AUTH_GOOGLE_ID and AUTH_GOOGLE_SECRET
  ],
  callbacks: {
    session: ({ session, user }) => ({
      ...session,
      user: { ...session.user, id: user.id },
    }),
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
})
```

#### lib/db.ts
```ts
import { PrismaClient } from "@prisma/client"

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const db =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"],
  })

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = db
```

#### prisma/schema.prisma
```prisma
generator client {
  provider = "prisma-client"   // v7: replaces prisma-client-js
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id            String    @id @default(cuid())
  name          String?
  email         String    @unique
  emailVerified DateTime?
  image         String?
  accounts      Account[]
  sessions      Session[]
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
}

model Account {
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String? @db.Text
  access_token      String? @db.Text
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String? @db.Text
  session_state     String?
  user              User    @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerAccountId])
}

model Session {
  id           String   @id @default(cuid())
  sessionToken String   @unique
  userId       String
  expires      DateTime
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)
}
```

#### prisma/config.ts
```ts
import path from "node:path"
import { defineConfig } from "prisma/config"

export default defineConfig({
  earlyAccess: true,
  schema: path.join("prisma", "schema.prisma"),
})
```

#### server/trpc.ts
```ts
import { initTRPC, TRPCError } from "@trpc/server"
import { auth } from "@/lib/auth"
import { db } from "@/lib/db"
import superjson from "superjson"
import { ZodError } from "zod"

export const createTRPCContext = async (opts: { headers: Headers }) => {
  const session = await auth()
  return { db, session, ...opts }
}

const t = initTRPC.context<typeof createTRPCContext>().create({
  transformer: superjson,
  errorFormatter({ shape, error }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        zodError: error.cause instanceof ZodError ? error.cause.flatten() : null,
      },
    }
  },
})

export const createCallerFactory = t.createCallerFactory
export const createTRPCRouter = t.router

export const publicProcedure = t.procedure

export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.session?.user) throw new TRPCError({ code: "UNAUTHORIZED" })
  return next({ ctx: { ...ctx, session: { ...ctx.session, user: ctx.session.user } } })
})
```

#### trpc/react.tsx
```tsx
"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { httpBatchLink, loggerLink } from "@trpc/client"
import { createTRPCReact } from "@trpc/react-query"
import { useState } from "react"
import superjson from "superjson"
import { type AppRouter } from "@/server/api/root"

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30 * 1000 },
    },
  })

let clientQueryClientSingleton: QueryClient | undefined
const getQueryClient = () => {
  if (typeof window === "undefined") return createQueryClient()
  return (clientQueryClientSingleton ??= createQueryClient())
}

export const api = createTRPCReact<AppRouter>()

export function TRPCReactProvider({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient()
  const [trpcClient] = useState(() =>
    api.createClient({
      links: [
        loggerLink({
          enabled: (op) =>
            process.env.NODE_ENV === "development" ||
            (op.direction === "down" && op.result instanceof Error),
        }),
        httpBatchLink({
          transformer: superjson,
          url: `${process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"}/api/trpc`,
          headers: () => ({ "x-trpc-source": "nextjs-react" }),
        }),
      ],
    })
  )
  return (
    <QueryClientProvider client={queryClient}>
      <api.Provider client={trpcClient} queryClient={queryClient}>
        {children}
      </api.Provider>
    </QueryClientProvider>
  )
}
```

#### store/useAppStore.ts
```ts
import { create } from "zustand"
import { devtools, persist } from "zustand/middleware"

interface AppState {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        sidebarOpen: true,
        setSidebarOpen: (open) => set({ sidebarOpen: open }),
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      }),
      { name: "app-storage" }
    )
  )
)
```

#### .env.example
```env
# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
NODE_ENV="development"

# Database
DATABASE_URL="postgresql://postgres:password@localhost:5432/myapp"

# Auth (NextAuth v5 / Auth.js)
# Note: AUTH_URL is auto-detected in most envs, only needed behind a proxy
AUTH_SECRET=""              # openssl rand -base64 32
# AUTH_URL="http://localhost:3000"

# OAuth Providers (auto-detected by NextAuth from variable names)
AUTH_GITHUB_ID=""
AUTH_GITHUB_SECRET=""
AUTH_GOOGLE_ID=""
AUTH_GOOGLE_SECRET=""

# Docker DB
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="password"
POSTGRES_DB="myapp"
```

#### package.json
```json
{
  "name": "my-app",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "db:push": "prisma db push",
    "db:studio": "prisma studio",
    "db:generate": "prisma generate",
    "db:migrate": "prisma migrate dev",
    "prepare": "husky"
  },
  "dependencies": {
    "@auth/prisma-adapter": "^2.7.4",
    "@prisma/client": "^7.4.1",
    "@tanstack/react-query": "^5.67.0",
    "@trpc/client": "^11.10.0",
    "@trpc/react-query": "^11.10.0",
    "@trpc/server": "^11.10.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.475.0",
    "next": "^16.1.0",
    "next-auth": "^5.0.0-beta.25",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "sonner": "^2.0.1",
    "superjson": "^2.2.2",
    "tailwind-merge": "^3.0.1",
    "zod": "^3.24.1",
    "zustand": "^5.0.3"
  },
  "devDependencies": {
    "@commitlint/cli": "^19.6.1",
    "@commitlint/config-conventional": "^19.6.0",
    "@eslint/eslintrc": "^3.2.0",
    "@tailwindcss/vite": "^4.0.7",
    "@types/node": "^22.10.5",
    "@types/react": "^19.0.7",
    "@types/react-dom": "^19.0.3",
    "@vitejs/plugin-react": "^4.3.4",
    "eslint": "^9.18.0",
    "eslint-config-next": "^16.1.0",
    "husky": "^9.1.7",
    "lint-staged": "^15.3.0",
    "prettier": "^3.4.2",
    "prettier-plugin-tailwindcss": "^0.6.9",
    "prisma": "^7.4.1",
    "tailwindcss": "^4.0.7",
    "tw-animate-css": "^1.2.4",
    "typescript": "^5.8.2",
    "typescript-eslint": "^8.20.0",
    "vitest": "^3.0.4"
  }
}
```

---

## Golden Path 2: Next.js Static (Marketing)

**Use when:** Figma Make output is a landing page, marketing site, or purely presentational.

### Folder Structure

```
my-app/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   ├── sections/
│   │   ├── Hero.tsx
│   │   ├── Features.tsx
│   │   ├── Pricing.tsx
│   │   ├── Testimonials.tsx
│   │   └── CTA.tsx
│   ├── ui/
│   └── layout/
│       ├── Header.tsx
│       └── Footer.tsx
├── lib/
│   └── utils.ts
├── public/
├── next.config.ts
├── tsconfig.json
├── package.json
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Key Deltas from Fullstack

No `server/`, no `trpc/`, no `store/`, no `prisma/`, no `proxy.ts`. Deps are minimal. Tailwind + shadcn/ui still used for styling. Output is `export: "standalone"` (same Dockerfile works).

#### package.json (minimal)
```json
{
  "dependencies": {
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.475.0",
    "next": "^16.1.0",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "tailwind-merge": "^3.0.1"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.7",
    "tailwindcss": "^4.0.7",
    "tw-animate-css": "^1.2.4",
    "typescript": "^5.8.2"
  }
}
```

---

## Golden Path 3: T3 Stack

**Use when:** Figma Make output shows an authenticated, data-driven SaaS product — dashboards, admin panels.

### Folder Structure

```
my-app/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   └── settings/page.tsx
│   │   ├── api/
│   │   │   ├── auth/[...nextauth]/route.ts
│   │   │   └── trpc/[trpc]/route.ts
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/
│   │   └── layout/
│   │       ├── DashboardLayout.tsx
│   │       ├── Sidebar.tsx
│   │       └── TopBar.tsx
│   ├── server/
│   │   ├── api/
│   │   │   ├── root.ts
│   │   │   └── routers/
│   │   ├── auth.ts
│   │   └── db.ts
│   ├── trpc/
│   │   ├── react.tsx
│   │   └── server.ts
│   ├── store/
│   │   └── useAppStore.ts
│   ├── lib/
│   │   └── utils.ts
│   ├── hooks/
│   └── types/
│       └── index.ts
├── prisma/
│   ├── schema.prisma
│   └── config.ts
├── proxy.ts
├── .env.example
├── next.config.ts
├── tsconfig.json
├── package.json
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Key Reference Files (T3 delta)

#### src/components/layout/DashboardLayout.tsx
```tsx
"use client"

import { Sidebar } from "@/components/layout/Sidebar"
import { TopBar } from "@/components/layout/TopBar"
import { useAppStore } from "@/store/useAppStore"
import { cn } from "@/lib/utils"

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useAppStore()

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div
        className={cn(
          "flex flex-1 flex-col overflow-hidden transition-all duration-300",
          sidebarOpen ? "ml-64" : "ml-16"
        )}
      >
        <TopBar />
        <main className="flex-1 overflow-y-auto bg-muted/10 p-6">{children}</main>
      </div>
    </div>
  )
}
```

#### src/components/layout/Sidebar.tsx
```tsx
"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboard, Settings, Users, ChevronLeft } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAppStore } from "@/store/useAppStore"
import { Button } from "@/components/ui/button"

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Users", href: "/users", icon: Users },
  { label: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, toggleSidebar } = useAppStore()

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-full flex-col border-r bg-background transition-all duration-300",
        sidebarOpen ? "w-64" : "w-16"
      )}
    >
      <div className="flex h-16 items-center justify-between border-b px-4">
        {sidebarOpen && <span className="text-lg font-bold">App</span>}
        <Button variant="ghost" size="icon" onClick={toggleSidebar} className="ml-auto">
          <ChevronLeft
            className={cn("h-4 w-4 transition-transform", !sidebarOpen && "rotate-180")}
          />
        </Button>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="size-4 shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
```

---

## Golden Path 4: Vite + React SPA

**Use when:** Figma Make output is for an internal tool or client-only app that doesn't need SSR.

### Folder Structure

```
my-app/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── routes/
│   │   ├── index.tsx              ← React Router v7 route definitions
│   │   ├── Root.tsx
│   │   └── pages/
│   │       ├── HomePage.tsx
│   │       ├── DashboardPage.tsx
│   │       └── NotFoundPage.tsx
│   ├── components/
│   │   ├── ui/
│   │   └── layout/
│   ├── store/
│   │   └── useAppStore.ts
│   ├── lib/
│   │   ├── utils.ts
│   │   └── api.ts
│   ├── hooks/
│   ├── types/
│   │   └── index.ts
│   └── styles/
│       └── globals.css            ← Tailwind v4 CSS-first config
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Reference Files

#### src/main.tsx
```tsx
import React from "react"
import ReactDOM from "react-dom/client"
import { RouterProvider } from "react-router"
import { QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "sonner"
import { router } from "@/routes/index"
import { queryClient } from "@/lib/api"
import "@/styles/globals.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  </React.StrictMode>
)
```

#### src/routes/index.tsx
```tsx
import { createBrowserRouter } from "react-router"
import { Root } from "@/routes/Root"
import { HomePage } from "@/routes/pages/HomePage"
import { DashboardPage } from "@/routes/pages/DashboardPage"
import { NotFoundPage } from "@/routes/pages/NotFoundPage"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Root />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
])
```

#### src/lib/api.ts
```ts
import { QueryClient } from "@tanstack/react-query"

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8080/api"
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  })
  if (!response.ok) throw new Error(`API error: ${response.status} ${response.statusText}`)
  return response.json() as Promise<T>
}
```

#### src/styles/globals.css
```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-border: var(--border);
  --color-ring: var(--ring);
  --radius-lg: var(--radius);
  --radius-md: calc(var(--radius) - 2px);
  --radius-sm: calc(var(--radius) - 4px);
}

:root {
  --background: hsl(0 0% 100%);
  --foreground: hsl(0 0% 3.9%);
  --primary: hsl(221.2 83.2% 53.3%);
  --primary-foreground: hsl(210 40% 98%);
  --border: hsl(214.3 31.8% 91.4%);
  --ring: hsl(221.2 83.2% 53.3%);
  --radius: 0.5rem;
}

@layer base {
  * { @apply border-border outline-ring/50; }
  body { @apply bg-background text-foreground; }
}
```

#### vite.config.ts
```ts
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import path from "path"

export default defineConfig({
  plugins: [
    tailwindcss(),  // Tailwind v4 Vite plugin — replaces PostCSS approach
    react(),
  ],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": { target: "http://localhost:8080", changeOrigin: true },
    },
  },
})
```

#### package.json
```json
{
  "type": "module",
  "dependencies": {
    "@tanstack/react-query": "^5.67.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.475.0",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router": "^7.3.0",
    "sonner": "^2.0.1",
    "tailwind-merge": "^3.0.1",
    "zod": "^3.24.1",
    "zustand": "^5.0.3"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.7",
    "@types/react": "^19.0.7",
    "@types/react-dom": "^19.0.3",
    "@vitejs/plugin-react": "^4.3.4",
    "tailwindcss": "^4.0.7",
    "tw-animate-css": "^1.2.4",
    "typescript": "^5.8.2",
    "vite": "^6.1.0",
    "vitest": "^3.0.4"
  }
}
```

---

## Golden Path 5: Monorepo (pnpm Workspaces)

**Use when:** The project needs multiple apps sharing UI, DB, and config.

### Folder Structure

```
my-monorepo/
├── apps/
│   ├── web/                        ← Next.js Fullstack (golden path 1)
│   └── marketing/                  ← Next.js Static (golden path 2)
├── packages/
│   ├── ui/                         ← Shared shadcn/ui + Tailwind v4 components
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── index.ts
│   │   │   ├── styles/
│   │   │   │   └── globals.css     ← Shared Tailwind v4 tokens
│   │   │   └── lib/
│   │   │       └── utils.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── config/                     ← Shared ESLint + TS configs
│   │   ├── eslint/
│   │   │   ├── base.mjs
│   │   │   └── next.mjs
│   │   ├── typescript/
│   │   │   ├── base.json
│   │   │   └── next.json
│   │   └── package.json
│   └── db/                         ← Shared Prisma schema + client
│       ├── prisma/
│       │   ├── schema.prisma
│       │   └── config.ts
│       ├── src/
│       │   └── index.ts
│       ├── package.json
│       └── tsconfig.json
├── pnpm-workspace.yaml
├── package.json
├── .npmrc
├── docker-compose.yml
└── README.md
```

### Reference Files

#### pnpm-workspace.yaml
```yaml
packages:
  - "apps/*"
  - "packages/*"
```

#### .npmrc
```
auto-install-peers=true
shamefully-hoist=false
strict-peer-dependencies=false
```

#### package.json (root)
```json
{
  "name": "my-monorepo",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "pnpm --parallel dev",
    "build": "pnpm --filter ./packages/db build && pnpm --filter ./packages/ui build && pnpm --parallel --filter './apps/*' build",
    "lint": "pnpm -r lint",
    "typecheck": "pnpm -r typecheck",
    "test": "pnpm -r test",
    "clean": "pnpm -r clean && rm -rf node_modules",
    "prepare": "husky"
  },
  "devDependencies": {
    "@commitlint/cli": "^19.6.1",
    "@commitlint/config-conventional": "^19.6.0",
    "husky": "^9.1.7",
    "lint-staged": "^15.3.0",
    "prettier": "^3.4.2",
    "prettier-plugin-tailwindcss": "^0.6.9",
    "typescript": "^5.8.2"
  },
  "engines": {
    "node": ">=22.0.0",
    "pnpm": ">=9.0.0"
  }
}
```

#### packages/config/typescript/base.json
```json
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  }
}
```

#### packages/config/typescript/next.json
```json
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "extends": "./base.json",
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "ES2022"],
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "noEmit": true,
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  }
}
```

#### packages/ui/package.json
```json
{
  "name": "@company/ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "scripts": {
    "lint": "eslint .",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.475.0",
    "tailwind-merge": "^3.0.1"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.7",
    "tailwindcss": "^4.0.7",
    "tw-animate-css": "^1.2.4"
  },
  "peerDependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0"
  }
}
```

#### packages/db/package.json
```json
{
  "name": "@company/db",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "scripts": {
    "db:push": "prisma db push",
    "db:migrate": "prisma migrate dev",
    "db:studio": "prisma studio",
    "db:generate": "prisma generate",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@prisma/client": "^7.4.1"
  },
  "devDependencies": {
    "prisma": "^7.4.1"
  }
}
```

#### apps/web/package.json (consuming monorepo packages)
```json
{
  "name": "@company/web",
  "dependencies": {
    "@company/ui": "workspace:*",
    "@company/db": "workspace:*"
  }
}
```

---

## MCP System Prompt Templates

### system.md

```md
You are a senior TypeScript engineer. Transform raw Figma Make generated code into
production-ready boilerplate following the company golden path exactly.

## Stack you are working with

- Next.js 16.1 (App Router) or Vite 6 + React 19.2
- Tailwind CSS v4 — CSS-first config, NO tailwind.config.ts
- shadcn/ui (Tailwind v4 build, no forwardRef)
- Zustand v5 for client state
- tRPC v11 + TanStack Query v5
- NextAuth v5 (AUTH_ env prefix)
- Prisma v7 (ESM, prisma-client generator, prisma.config.ts)
- React Router v7 for SPAs
- Vitest v3 for testing

## You always

- Follow the exact folder structure of the selected golden path
- Use TypeScript strict mode — no `any`, no implicit types
- Use `size-*` utility (e.g. `size-4`) instead of `w-4 h-4` — it's the Tailwind v4 way
- Use `@import "tailwindcss"` at the top of globals.css, never `@tailwind base/components/utilities`
- Declare design tokens using `@theme inline` and CSS custom properties
- Use `tw-animate-css` — never `tailwindcss-animate` (deprecated in Tailwind v4)
- Use shadcn/ui components directly, they accept `ref` as a regular prop (no forwardRef)
- Use Sonner for all toasts (import from "sonner")
- Use Zustand for all client state spanning multiple components
- Use `AUTH_` prefix for all auth env vars (not `NEXTAUTH_`)
- Use `proxy.ts` not `middleware.ts` for Next.js 16 auth guards
- Use `prisma-client` (not `prisma-client-js`) generator in schema.prisma
- Add a `prisma/config.ts` file in all Prisma projects
- Write async page params: `async function Page(props: { params: Promise<{ id: string }> })`
- Use pnpm, `"type": "module"` in package.json
- Add `// TODO:` comments when making assumptions

## You never

- Create a `tailwind.config.ts` file — Tailwind v4 has no JS config
- Use `@tailwind base`, `@tailwind components`, `@tailwind utilities` directives
- Use `tailwindcss-animate` — use `tw-animate-css` instead
- Use `h-4 w-4` when `size-4` works
- Use `forwardRef` in any component
- Use `NEXTAUTH_SECRET`, `NEXTAUTH_URL` — use `AUTH_SECRET`, `AUTH_URL`
- Use `middleware.ts` in Next.js 16 projects — use `proxy.ts`
- Use `prisma-client-js` generator — use `prisma-client`
- Install libraries not in the golden path package.json
- Leave inline styles in output
```

### manifest.json (Next.js Fullstack — v2)

```json
{
  "name": "nextjs-fullstack",
  "version": "2.0.0",
  "description": "Next.js 16 App Router + tRPC v11 + Prisma v7 + NextAuth v5 + Zustand v5 + Tailwind v4 + shadcn/ui",
  "triggers": {
    "hasAuth": ["login", "register", "signin", "signup", "auth", "forgot-password"],
    "hasDashboard": ["dashboard", "admin", "panel", "analytics", "overview"],
    "hasDataLists": ["table", "list", "grid", "feed", "users", "orders"],
    "hasSidebar": ["sidebar", "drawer", "navigation", "nav-rail"]
  },
  "routing": {
    "strategy": "app-router",
    "pageKeywords": ["page", "screen", "view", "route"],
    "asyncParams": true,
    "groupKeywords": {
      "(auth)": ["login", "register", "signup", "signin"],
      "(dashboard)": ["dashboard", "admin", "settings", "profile"]
    }
  },
  "tailwind": {
    "version": 4,
    "configFile": null,
    "cssFile": "app/globals.css",
    "tokenDirective": "@theme inline",
    "animatePackage": "tw-animate-css"
  },
  "tokenTargets": ["app/globals.css"],
  "requiredFiles": [
    "app/layout.tsx",
    "app/globals.css",
    "lib/utils.ts",
    "lib/db.ts",
    "lib/auth.ts",
    "server/trpc.ts",
    "server/api/root.ts",
    "trpc/react.tsx",
    "store/useAppStore.ts",
    "prisma/schema.prisma",
    "prisma/config.ts",
    "next.config.ts",
    "tsconfig.json",
    "package.json",
    ".env.example",
    "Dockerfile",
    "docker-compose.yml",
    "README.md",
    "eslint.config.mjs",
    ".prettierrc",
    "commitlint.config.mjs"
  ],
  "optionalFiles": {
    "hasAuth": [
      "app/(auth)/login/page.tsx",
      "app/(auth)/register/page.tsx",
      "app/api/auth/[...nextauth]/route.ts",
      "proxy.ts"
    ],
    "hasDashboard": ["app/(dashboard)/layout.tsx", "app/(dashboard)/dashboard/page.tsx"],
    "hasSidebar": ["components/layout/Sidebar.tsx"],
    "hasDataLists": ["types/index.ts"]
  }
}
```

---

## Design Token Extraction Rules for Tailwind v4

⚠️ Tailwind v4 has no JS config. ALL token extraction goes to `globals.css` only.

**Pattern to follow:**

```css
/* 1. Declare raw values as CSS custom properties in :root */
:root {
  --primary: hsl(221.2 83.2% 53.3%);
  --background: hsl(0 0% 100%);
}

/* 2. Map them to Tailwind v4 theme via @theme inline */
@theme inline {
  --color-primary: var(--primary);
  --color-background: var(--background);
}
```

**Naming convention for extracted tokens:**

| Raw Figma value | CSS variable | Tailwind class |
|---|---|---|
| Most-used color | `--primary` | `bg-primary`, `text-primary` |
| Second-most-used | `--secondary` | `bg-secondary` |
| Near-white bg | `--background` | `bg-background` |
| Near-black text | `--foreground` | `text-foreground` |
| Borders | `--border` | `border-border` |
| Input states | `--input` | `border-input` |
| Focus rings | `--ring` | `ring-ring` |

**Spacing:** Figma Make pixel values cluster to Tailwind's default scale. Only add custom tokens for values clearly outside the default scale (not 4, 8, 12, 16, 24, 32, 48, 64 px).

**Border radius:** Map to `--radius` base token, derive `sm/md/lg/xl` via `calc()`.

---

## Component Classification Quick Reference

| Name contains | Maps to |
|---|---|
| Page, Screen, View | `app/[route]/page.tsx` |
| Layout, Shell | `app/[route]/layout.tsx` |
| Header, Navbar, TopBar | `components/layout/Header.tsx` |
| Footer | `components/layout/Footer.tsx` |
| Sidebar, Drawer, Rail | `components/layout/Sidebar.tsx` |
| Hero, Features, Pricing, CTA, FAQ | `components/sections/` |
| Button, Badge, Tag, Chip | `components/ui/button.tsx` (shadcn) |
| Card, Tile, Panel | `components/ui/card.tsx` (shadcn) |
| Input, Field, Select, Checkbox | `components/ui/input.tsx` (shadcn) |
| Modal, Dialog, Sheet | `components/ui/dialog.tsx` (shadcn) |
| Table, DataGrid, List | `components/ui/table.tsx` (shadcn) |
| Avatar, Profile icon | `components/ui/avatar.tsx` (shadcn) |
| Everything else | `components/ui/` |

---

## Generation Report Template (README.md)

```md
# [Project Name] — Generated Boilerplate

Generated from Figma Make source using the **[golden-path-name]** golden path.
Stack: Next.js 16 · React 19.2 · Tailwind v4 · shadcn/ui · tRPC v11 · Prisma v7 · NextAuth v5 · Zustand v5

## Getting Started

\`\`\`bash
pnpm install
cp .env.example .env
# Fill in AUTH_SECRET, DATABASE_URL, and OAuth provider IDs in .env
pnpm db:push
pnpm db:generate
pnpm dev
\`\`\`

## What Was Generated

- **Components:** [n] (ui: [n], layout: [n], sections: [n])
- **Routes inferred:** [list]
- **Design tokens extracted:** [n] colors, [n] spacing, [n] typography
- **Optional features enabled:** [auth / dashboard / sidebar / etc.]

## ⚠️ TODOs Before Shipping

[auto-generated list of all // TODO: comments across the project]

## Stack
| | |
|---|---|
| Framework | Next.js 16.1 |
| React | 19.2 |
| Styling | Tailwind CSS v4 + shadcn/ui |
| State | Zustand v5 |
| API | tRPC v11 + TanStack Query v5 |
| Auth | NextAuth v5 |
| ORM | Prisma v7 |
| Testing | Vitest v3 |
```
