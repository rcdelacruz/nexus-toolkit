# Golden Path Selection Guide

A practical guide for decision makers choosing the right golden path when using the Nexus MCP pipeline.

---

## Quick-Select Table

| I need… | Choose |
|---------|--------|
| A marketing site / landing page / docs site | `nextjs-static` |
| A full-stack SaaS or internal tool (one app) | `nextjs-fullstack` |
| A full-stack app with T3 community conventions | `t3-stack` |
| A client-side tool / dashboard with an existing separate backend | `vite-spa` |
| Multiple apps (web + marketing) sharing a design system and database | `monorepo` |
| Multiple apps (web + native mobile iOS/Android) with Supabase backend | `full-stack-rn` |
| Multiple apps (web + native mobile iOS/Android) with Flutter + Supabase backend | `full-stack-flutter` |

---

## Decision Tree

```
Does the project need a backend (auth, database, API)?
│
├── NO
│   └── Does it need client-side routing between pages?
│       ├── NO  → nextjs-static
│       │         (landing pages, marketing, docs, portfolios)
│       └── YES → vite-spa
│                 (tools with a separate existing API, or purely client-side apps)
│
└── YES
    └── Is this a single app or multiple apps?
        │
        ├── SINGLE APP
        │   └── Do you prefer the T3 community conventions (src/ directory, T3 idioms)?
        │       ├── YES → t3-stack
        │       └── NO  → nextjs-fullstack
        │
        └── MULTIPLE APPS or MULTIPLE TEAMS
            └── Does the project include a native mobile app (iOS/Android)?
                ├── YES
                │   └── Flutter (Dart) or React Native?
                │       ├── Flutter → full-stack-flutter
                │       │            (Next.js web + Flutter mobile, Supabase)
                │       └── React Native → full-stack-rn
                │                          (Next.js web + Expo mobile, Supabase)
                └── NO  → monorepo
                          (web + marketing, Prisma + NextAuth)
```

---

## Golden Path Profiles

### `nextjs-static`
**Best for:** Marketing sites, landing pages, documentation portals, portfolios, campaign pages.

**What it gives you:**
- Next.js with `output: "export"` — generates a pure static HTML/CSS/JS bundle
- Tailwind v4 + shadcn/ui components
- Zero server-side code — no auth, no database, no API routes
- Deploys to any CDN (Vercel, Netlify, S3 + CloudFront, GitHub Pages)

**When to choose it:**
- The Figma design is a marketing or informational site
- No user accounts or personalized content
- Content is either static or fetched client-side from a third-party API (CMS, etc.)
- Fastest possible page loads and cheapest hosting are priorities

**When NOT to choose it:**
- Users need to log in
- Content is user-generated or personalized
- You need server-side rendering (SEO for dynamic content)

---

### `nextjs-fullstack`
**Best for:** SaaS applications, internal tools, B2B dashboards, admin panels, any app where users log in and interact with their own data.

**What it gives you:**
- Next.js App Router with SSR and RSC (React Server Components)
- Authentication via NextAuth v5 (supports GitHub, Google, credentials, etc.)
- Database via Prisma v7 + PostgreSQL
- Type-safe API via tRPC v11 (server → client, no REST boilerplate)
- Client state via Zustand v5
- Notifications via Sonner
- Single deployable unit — one app, one database

**When to choose it:**
- The Figma design is a product (SaaS, internal tool, dashboard)
- Users have accounts and their own data
- You want end-to-end type safety from database schema to UI component
- You want everything in one codebase with minimal infrastructure complexity

**When NOT to choose it:**
- You already have a backend in another language/framework (use `vite-spa` instead)
- You have multiple distinct apps that share UI components (use `monorepo` instead)
- It's just a marketing site (use `nextjs-static` instead)

---

### `t3-stack`
**Best for:** Same use cases as `nextjs-fullstack`, but for teams already familiar with the T3 ecosystem or projects that will be handed off to T3 community developers.

**What it gives you:**
- Identical stack to `nextjs-fullstack`: tRPC + Prisma + NextAuth + Zustand + Tailwind v4
- T3 conventions: all source code lives under `src/`, T3-style file organization
- The standard that thousands of T3 developers already know

**`t3-stack` vs `nextjs-fullstack` — pick one, not both:**

| | `nextjs-fullstack` | `t3-stack` |
|---|---|---|
| Source directory | project root (`app/`, `components/`, `lib/`) | `src/` (`src/app/`, `src/components/`, `src/lib/`) |
| Convention origin | Nexus enterprise standard | T3 community standard |
| Best handoff to | Any Next.js developer | T3 community developers |
| Functional difference | None | None |

**When to choose it:**
- The team is already T3-native
- The project will be handed off to a T3 developer or agency
- You want the community resources, templates, and examples from the T3 ecosystem

**When NOT to choose it:**
- Your team has no preference — default to `nextjs-fullstack` (slightly simpler root structure)

---

### `vite-spa`
**Best for:** Client-side tools, dashboards that consume an existing API, internal utilities, browser-based apps where SSR is not needed.

**What it gives you:**
- Vite 6 build tool (no Next.js, no SSR, no server-side code)
- React Router v7 for client-side navigation
- TanStack Query for data fetching against any REST/GraphQL/tRPC API
- Zustand for client state
- Tailwind v4 + shadcn/ui components
- Deploys to any static host — the output is just `index.html` + assets

**When to choose it:**
- You already have a backend (Django, Rails, FastAPI, Express, etc.) and just need a frontend
- SSR / SEO is not a requirement (internal tools, authenticated dashboards, etc.)
- The team wants the simplest possible setup — no server concepts at all
- You need to embed the app in a native shell (Electron, Capacitor, etc.)

**When NOT to choose it:**
- SEO matters — Vite SPA has no SSR, so search engines see a blank page without extra config
- You need auth baked in — add it yourself or pick a fullstack golden path
- Content is highly dynamic and public-facing

---

### `monorepo`
**Best for:** Products that ship multiple distinct apps to the same end users, or organizations with multiple teams that need to share a design system, database schema, and configuration.

**What it gives you:**
- Turborepo pnpm workspace with two apps and shared packages:
  - `apps/web` — full-stack Next.js app (same stack as `nextjs-fullstack`)
  - `apps/marketing` — Next.js static export (same stack as `nextjs-static`)
  - `packages/ui` — shared React component library (Button, Card, Input, utils)
  - `packages/db` — shared Prisma client (one schema, one generated client, used by both apps)
  - `packages/config` — shared TypeScript + ESLint configs
- One `pnpm install` installs everything
- One CI pipeline builds and tests everything
- Docker-ready with per-app Dockerfiles using monorepo root build context

**When to choose it:**
- The project has both a **product app** and a **marketing site** that share branding/components
- Multiple teams work on different surfaces but must use a consistent design system
- You want a single source of truth for the database schema across all apps
- The org is scaling and needs workspace-level tooling (Turborepo caching, etc.)

**When NOT to choose it:**
- You only have one app — the added complexity of a monorepo is not justified
- The team is small and the overhead of workspace management is a burden
- The apps have nothing in common — separate repos are cleaner

---

### `full-stack-rn`
**Best for:** B2B SaaS, consumer apps, or internal tools that need both a web dashboard and native iOS/Android apps backed by the same Supabase database with RBAC and audit logging.

**What it gives you:**
- Turborepo pnpm workspace with two apps and four shared packages:
  - `apps/web` — Next.js 16 App Router: REST API + Supabase backend + dashboard UI
  - `apps/mobile` — Expo 54 bare workflow: NativeWind UI, authenticates with Supabase directly, calls `apps/web` REST API
  - `packages/ui` — shared web React components (shadcn/ui + Tailwind v4)
  - `packages/ui-native` — shared native components (NativeWind primitives)
  - `packages/supabase` — shared Supabase client helpers, DB types, RBAC helpers, audit logger
  - `packages/config` — shared TypeScript + ESLint configs
- Supabase replaces Prisma + NextAuth entirely (auth + database + RLS + realtime + storage)
- RBAC via `user_roles` table + `hasPermission()` helper enforced in Route Handlers
- Audit logging via `audit_logs` table + `logAuditEvent()` on every mutation
- Turborepo remote cache enabled for fast CI/CD across large teams
- One `pnpm install` installs everything; one `turbo run build` builds everything

**API boundary**: `apps/mobile` authenticates directly with Supabase (gets a JWT), then sends that JWT as a Bearer token to `apps/web/app/api/v1/` Route Handlers. `apps/web` verifies the JWT server-side and handles all business logic.

**When to choose it:**
- The product needs both a web dashboard and native iOS/Android apps
- Supabase is the chosen backend (auth + database + storage)
- RBAC and audit logging are hard requirements
- Multiple teams (web team + mobile team) share a design system and API contract
- You want Turborepo remote cache for large monorepo builds

**When NOT to choose it:**
- No mobile app needed — use `monorepo` (Prisma + NextAuth) or `nextjs-fullstack`
- You prefer Prisma + NextAuth over Supabase — use `monorepo` instead
- The mobile app only needs read-only data — `vite-spa` + Expo REST client is simpler
- The team is small and the monorepo overhead is not justified

**Deployment:**
- Web: `apps/web/Dockerfile` (standalone Next.js) → Docker/VPS or Vercel
- Mobile: EAS Build (`eas build --platform all`) → App Store + Google Play

---

### `full-stack-flutter`
**Best for:** Products that need both a web dashboard and native iOS/Android apps, where the mobile team prefers Flutter/Dart over React Native.

**What it gives you:**
- Turborepo pnpm workspace with two apps and shared packages:
  - `apps/web` — Next.js 16 App Router: REST API + Supabase backend + dashboard UI (TypeScript)
  - `apps/mobile` — Flutter 3.32 standalone Dart project: Riverpod state, go_router navigation, Material 3 UI
  - `packages/ui-primitives` — design tokens (TypeScript constants; consumed by web only)
  - `packages/ui-web` — shadcn/ui + Tailwind v4 (web only)
  - `packages/shared` — types, utils, Zod schemas (web only)
  - `packages/supabase` — Supabase client + DB types + RBAC + audit helpers (web only)
  - `packages/config` — shared TypeScript + ESLint configs
- Flutter is **outside** the pnpm workspace — managed by `pub`/`pubspec.yaml`
- Mobile env vars via `--dart-define-from-file=.env.json`
- Supabase replaces Prisma + NextAuth (auth + database + RLS)
- Same API boundary as `full-stack-rn`: mobile authenticates with Supabase (JWT), calls `apps/web` REST API with Bearer token

**When to choose it:**
- The product needs both a web dashboard and native iOS/Android apps
- The mobile team knows Flutter/Dart (or prefers it over React Native)
- Supabase is the chosen backend
- You want Material 3 UI on mobile with full Dart ecosystem access

**When NOT to choose it:**
- The mobile team knows React Native — use `full-stack-rn` instead
- No mobile app needed — use `monorepo` or `nextjs-fullstack`
- The team is small and monorepo overhead is not justified

**Deployment:**
- Web: `apps/web/Dockerfile` (standalone Next.js) → Docker/VPS or Vercel
- Mobile: `flutter build ipa` (iOS) / `flutter build apk` (Android) → App Store + Google Play

---

## Common Mistakes

| Mistake | Why it happens | Correct choice |
|---------|---------------|----------------|
| Using `monorepo` for a single product | "More structure = more enterprise" | `nextjs-fullstack` or `t3-stack` |
| Using `vite-spa` when SEO matters | "Simpler is better" | `nextjs-fullstack` or `nextjs-static` |
| Using `nextjs-static` for an app with user accounts | "We can add auth later" | `nextjs-fullstack` — retrofitting auth onto a static export is a full rewrite |
| Using `nextjs-fullstack` AND `t3-stack` in the same org | "Pick what each team likes" | Pick one org-wide — splitting conventions creates knowledge silos |
| Using `monorepo` but only building `apps/web` | "We might need marketing later" | `nextjs-fullstack` — migrate to monorepo when the second app is actually needed |
| Using `full-stack-rn` without a native app | "Future-proofing" | `nextjs-fullstack` or `monorepo` — the Expo setup adds significant complexity for no benefit |
| Using `monorepo` when you need native mobile | "We'll add React Native later" | `full-stack-rn` — retrofitting Expo into a `monorepo` requires replacing Prisma + NextAuth with Supabase |
| Using `full-stack-flutter` when the mobile team knows React Native | "Flutter is more native" | `full-stack-rn` — use the framework the team already knows |

---

## Deployment Compatibility

| Golden Path | Vercel | Docker / VPS | S3 + CDN | Netlify |
|---|---|---|---|---|
| `nextjs-static` | ✅ | ✅ (nginx) | ✅ | ✅ |
| `nextjs-fullstack` | ✅ | ✅ (standalone) | ❌ (needs server) | ❌ |
| `t3-stack` | ✅ | ✅ (standalone) | ❌ | ❌ |
| `vite-spa` | ✅ | ✅ (nginx) | ✅ | ✅ |
| `monorepo` | ✅ | ✅ (per-app Dockerfile) | ✅ (marketing only) | ✅ (marketing only) |
| `full-stack-rn` | ✅ (web) | ✅ (standalone) | ❌ | ❌ |
| `full-stack-flutter` | ✅ (web) | ✅ (standalone) | ❌ | ❌ |

---

## At a Glance — Complexity vs Capability

```
Complexity
    │
    │  full-stack-flutter ─────────────────────── web + Flutter mobile, Supabase
    │  full-stack-rn ──────────────────────────── web + RN/Expo mobile, Supabase
    │  monorepo ──────────────────────────────── multiple apps, shared infra
    │
    │  nextjs-fullstack ──────────── full-stack SaaS, auth + DB + API
    │  t3-stack ─────────────────── same, T3 conventions
    │
    │  vite-spa ──────────────────── client-side only, existing backend
    │
    │  nextjs-static ─────────────── marketing / static content
    │
    └──────────────────────────────────────────── Capability / Requirements
```

Start with the simplest golden path that meets the project's requirements.
Migrate up when you outgrow it — not before.
