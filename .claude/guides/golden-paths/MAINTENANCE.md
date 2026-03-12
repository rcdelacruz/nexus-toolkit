# Golden Path Maintenance Guide

This document covers how to keep the golden path boilerplates healthy over time.

---

## The Two Sources of Truth

Every golden path has two places that describe its stack. **Both must stay in sync.**

| File | Controls |
|------|----------|
| `golden_paths/{name}/reference/package.json` | What actually gets installed in the generated project |
| `.claude/agents/{name}.md` — Stack table | What the LLM is instructed to code against |

If they drift, the LLM generates code targeting a version that doesn't match what gets installed.

---

## What Updates Itself (Zero Maintenance)

All `package.json` entries use `^` (caret) ranges. Every user who runs `pnpm install` on a
generated project automatically gets the latest compatible patch/minor at that moment.

You do **not** need to chase patch releases manually. `^16.1.0` already resolves to `16.1.6`.

---

## What Requires Manual Updates

| Trigger | What to update |
|---------|---------------|
| New **major** version drops (e.g. React 20, Next.js 17) | `package.json` floor + typecheck + agent Stack table if API changed |
| **Breaking minor** in a fast-moving package | Same as above |
| **Security advisory** on a pinned dep | Bump the floor (e.g. `^7.4.0` → `^7.4.2`) |
| Beta package reaches stable (e.g. `^5.0.0-beta.x` → `^5.0`) | Update version spec |
| Agent generates incorrect code for a package's current API | Update rules/examples in agent `.md` |

---

## Quarterly Sweep Process

Run this in each `golden_paths/{name}/reference/` that has a `package.json`:

```bash
# 1. See what has drifted
pnpm dlx npm-check-updates --target minor   # safe: minor/patch only
pnpm dlx npm-check-updates --target latest  # careful: includes majors

# 2. Apply minor/patch bumps
pnpm dlx npm-check-updates --target minor -u
pnpm install --ignore-scripts

# 3. For Prisma projects — regenerate the client
pnpm db:generate

# 4. Typecheck — must pass with zero errors
pnpm typecheck

# 5. If typecheck passes, commit. If not, fix before committing.
```

For the **monorepo**, run from the monorepo root:
```bash
pnpm install --ignore-scripts
pnpm --filter @company/db db:generate
pnpm typecheck   # runs all packages in parallel
```

For **full-stack-rn**, run from the monorepo root:
```bash
pnpm install --ignore-scripts
supabase gen types typescript --local > packages/supabase/src/types/database.ts
pnpm typecheck   # web + supabase + ui packages only; mobile requires Metro bundler
# Note: pnpm --filter @company/mobile typecheck requires Expo Metro setup — skip on CI
# if Expo is not installed, or run it inside the Expo dev environment
```

---

## When to Update Agent `.md` Files

The Stack table version numbers in `.claude/agents/{name}.md` only need updating when:

- A **new major** ships with API changes the LLM needs to know about
- The **import path, hook name, or config structure** of a package changes
- A package the LLM references is **added or removed** from the boilerplate

They do **not** need updating for patch/minor bumps with no API surface changes.
Example: `@trpc/server 11.10.0 → 11.11.0` — no update needed. `tRPC 12.0` with a rewritten
router API — update needed.

---

## Keeping Versions Consistent Across Golden Paths

Shared packages (React, Tailwind, tRPC, TanStack Query, Zod, etc.) must be on the same
version across all golden paths that use them. Inconsistencies confuse the pipeline.

Quick audit:
```bash
grep -r '"@tanstack/react-query"' golden_paths/*/reference/package.json
grep -r '"@trpc/server"' golden_paths/*/reference/package.json
grep -r '"next-auth"' golden_paths/*/reference/package.json
```

---

## Known Breaking Patterns (Lessons Learned)

### Prisma 7
- Remove `url = env("DATABASE_URL")` from `datasource` in `schema.prisma` — moved to `prisma/config.ts`
- Generator must be `prisma-client` (not `prisma-client-js`) and requires explicit `output`
- `schema` path in `prisma/config.ts` is relative to the config file's own directory
- Import `PrismaClient` from the generated path, not `@prisma/client`
- Requires `@prisma/adapter-pg` + `pg` + `@types/pg`
- Generated files (`/generated/`, `/src/generated/`) must be in `.gitignore`

### tRPC v11 RSC (`createHydrationHelpers`)
- `appRouter` must have at least one procedure — an empty `createTRPCRouter({})` breaks the
  type guard (`AnyRouter extends {}` evaluates to `true`, triggering `TypeError<...>`)
- Fix: keep `server/api/routers/example.ts` with a `hello` query in the boilerplate

### Tailwind v4
- No `tailwind.config.ts` — config is CSS-first in `globals.css`
- Next.js projects need `@tailwindcss/postcss` + `postcss.config.mjs`
- Vite projects need `@tailwindcss/vite` plugin
- `tw-animate-css` uses `@import` (CSS), not `@plugin` (JS)
- All color values must be `hsl()` — never `oklch()`, `rgb()`, or `#hex`

### NextAuth v5
- `AUTH_SECRET` not `NEXTAUTH_SECRET`
- No `NEXTAUTH_URL` needed
- Use `proxy.ts` at project root, not `middleware.ts`

### monorepo packages/ui
- Must use `react-library.json` tsconfig (`moduleResolution: bundler`) not `base.json` (`NodeNext`)
- `packages/config/package.json` exports must include `./typescript/react-library.json`
- `@types/node` required in devDependencies (for `process.env`)

### Next.js `experimental.reactCompiler`
- Requires `babel-plugin-react-compiler` — do not include in base boilerplate
- Causes TypeScript type errors in `next.config.ts` when the Babel plugin is not installed

### Next.js `async headers()` incompatible with `output: "export"`

Adding `async headers()` to `next.config.ts` when `output: "export"` is set causes a Next.js build error:
```
Error: export has been marked as having an unsupported configuration: headers
```
Static export golden paths must document security headers as CDN/hosting-layer config (Vercel `vercel.json`, Cloudflare `_headers` file, Nginx `add_header` directives) rather than in `next.config.ts`.

### full-stack-rn: NativeWind v4 uses Tailwind v3 (not v4)
- `apps/mobile/global.css` must use `@tailwind base; @tailwind components; @tailwind utilities;` (Tailwind v3 syntax)
- Using `@import "tailwindcss"` (Tailwind v4 syntax) in mobile will break the NativeWind build entirely
- `apps/web/app/globals.css` and `packages/ui/src/styles/globals.css` use `@import "tailwindcss"` (v4) — these are separate files

### full-stack-rn: expo-secure-store version
- `expo-secure-store ^15.0.8` is correct for Expo SDK 54 — do not use `^14.x`
- Expo SDK version pins its package versions; match them from the Expo SDK 54 changelog

### full-stack-rn: Supabase type generation
- `supabase gen types typescript` must be re-run after every schema migration
- The placeholder `packages/supabase/src/types/database.ts` covers `user_roles` and `audit_logs` only
- Generated file replaces the placeholder — never manually edit the generated file

### full-stack-rn: packages/supabase isomorphic boundary
- `src/client/server.ts` uses Next.js `cookies()` — it is Next.js-only, never import in mobile
- `src/client/mobile.ts` uses expo-secure-store adapter — it is RN-only, never import in web server code
- `src/client/browser.ts` uses `@supabase/ssr` `createBrowserClient` — web client components only

---

## File Checklist for a New Golden Path

When adding a new golden path, ensure these exist:

- [ ] `golden_paths/{name}/reference/` — boilerplate files
- [ ] `golden_paths/{name}/reference/.gitignore` — includes `node_modules`, `/generated/`, build dirs
- [ ] `golden_paths/{name}/reference/package.json` — `^` ranges, consistent with other paths
- [ ] `golden_paths/{name}/manifest.json` — required files list
- [ ] `.claude/agents/{name}.md` — Stack table matches `package.json` versions
- [ ] `golden_paths/{name}/reference/.nvmrc` — Node version pin
- [ ] `golden_paths/{name}/reference/LICENSE` — MIT with `__YEAR__` / `__AUTHOR__` placeholders
- [ ] `golden_paths/{name}/reference/CHANGELOG.md` — Keep a Changelog stub
- [ ] `golden_paths/{name}/reference/CONTRIBUTING.md` — branch naming, workflow, commit format
- [ ] `golden_paths/{name}/reference/.github/dependabot.yml`
- [ ] `golden_paths/{name}/reference/.github/PULL_REQUEST_TEMPLATE.md`
- [ ] `golden_paths/{name}/reference/.github/ISSUE_TEMPLATE/bug_report.md`
- [ ] `golden_paths/{name}/reference/.github/ISSUE_TEMPLATE/feature_request.md`
- [ ] `golden_paths/{name}/reference/.github/workflows/ci.yml` (all steps commented out)
- [ ] Security headers in `next.config.ts` (standalone) or CDN comments (export)
- [ ] `/api/health` route (server golden paths only)
- [ ] `golden_paths/{name}/manifest.json` has `classification.categories` covering all Figma component types
- [ ] `pnpm install && pnpm typecheck` passes with zero errors
