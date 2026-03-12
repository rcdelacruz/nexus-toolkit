# Golden Paths — Reference

A golden path defines the target tech stack, folder structure, and boilerplate for a Nexus pipeline output.
All rules, conventions, and code quality requirements live in the corresponding agent file at `.claude/agents/{name}.md`.

| Name | Agent File | Description |
|------|-----------|-------------|
| `nextjs-fullstack` | `.claude/agents/nextjs-fullstack.md` | Next.js 16.1 App Router + React 19.2 + Tailwind v4 + tRPC v11 + Prisma v7 + NextAuth v5 + Zustand v5. Full-stack with auth, database, and API layer. |
| `nextjs-static` | `.claude/agents/nextjs-static.md` | Next.js 16.1 static export + React 19.2 + Tailwind v4 + CVA. No server-side features — marketing sites, landing pages, documentation. |
| `t3-stack` | `.claude/agents/t3-stack.md` | Next.js 16.1 + tRPC v11 + Prisma v7 + NextAuth v5 + Zustand v5 + Tailwind v4. All app code under `src/`. T3-style monolith with dashboard layout. |
| `vite-spa` | `.claude/agents/vite-spa.md` | Vite 6 + React 19.2 + React Router v7 + Tailwind v4 + Zustand v5 + TanStack Query v5. Pure client-side SPA, no server components. |
| `monorepo` | `.claude/agents/monorepo.md` | Turborepo pnpm workspace — `apps/web` (fullstack), `apps/marketing` (static), `packages/ui` (shared components), `packages/db` (Prisma), `packages/config`. |
| `full-stack-rn` | `.claude/agents/full-stack-rn.md` | Turborepo monorepo — `apps/web` (Next.js 16 + Supabase REST API), `apps/mobile` (Expo 54 bare + NativeWind), `packages/ui-primitives` (design tokens), `packages/ui-web` (shadcn/Tailwind v4), `packages/ui-mobile` (NativeWind/Tailwind v3), `packages/shared` (types/utils), `packages/supabase`, `packages/config`. No tRPC/Prisma/NextAuth. |
| `full-stack-flutter` | `.claude/agents/full-stack-flutter.md` | Turborepo monorepo — `apps/web` (Next.js 16 + Supabase REST API), `apps/mobile` (Flutter 3.32 + Dart, Riverpod, go_router), `packages/ui-primitives` (design tokens), `packages/ui-web` (shadcn/Tailwind v4), `packages/shared` (types/utils), `packages/supabase`, `packages/config`. Flutter is outside pnpm workspace. No tRPC/Prisma/NextAuth. |

## What lives in `golden_paths/{name}/`

| Asset | Purpose |
|-------|---------|
| `manifest.json` | Stack metadata: required files list, globals.css path, Tailwind animate package, classification rules (under the `classification` key) |
| `reference/` | Boilerplate files copied verbatim into every new project (configs, layout, lib, etc.) |

## What does NOT live here

- **Rules and conventions** → agent file at `.claude/agents/{name}.md`
- **Prompts and context engineering** → agent file at `.claude/agents/{name}.md`
- **Transformation instructions** → built inline by `remap.py` from Figma source + written into `05_queue/` (one file per component)
