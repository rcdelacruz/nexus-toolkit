# __PROJECT_NAME__

__PROJECT_DESCRIPTION__

## Workspace Structure

```
apps/
├── web/          # Full-stack Next.js app — authenticated dashboard + tRPC API
└── marketing/    # Static Next.js marketing site — public-facing pages

packages/
├── ui/           # Shared React component library (shadcn/ui + Tailwind v4)
├── db/           # Shared Prisma schema, client, and migration scripts
└── config/       # Shared ESLint + TypeScript configurations
```

## Tech Stack

| | |
|---|---|
| Monorepo | pnpm workspaces |
| Apps framework | Next.js 16.1 (App Router) |
| Language | TypeScript 5 (strict) |
| Styling | Tailwind CSS v4 + shadcn/ui |
| API | tRPC v11 + TanStack Query v5 |
| Auth | NextAuth v5 |
| ORM | Prisma v7 (PostgreSQL) |
| State | Zustand v5 |
| Linting | ESLint 9 (shared config in `packages/config`) |
| Formatting | Prettier 3 + prettier-plugin-tailwindcss |
| Git hooks | Husky + lint-staged + commitlint |

## Getting Started

**Prerequisites:** Node.js 22+, pnpm 9+, Docker (for local Postgres)

```bash
# 1. Install all workspace dependencies
pnpm install

# 2. Copy and fill in environment variables for each app
cp apps/web/.env.example apps/web/.env
cp apps/marketing/.env.example apps/marketing/.env

# 3. Start the local database
docker compose up -d

# 4. Apply the database schema and generate the Prisma client
pnpm db:migrate
pnpm db:generate

# 5. Start all apps in parallel
pnpm dev
```

- `apps/web` runs on [http://localhost:3000](http://localhost:3000)
- `apps/marketing` runs on [http://localhost:3001](http://localhost:3001)

## Available Scripts

Run from the workspace root:

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start all apps in parallel |
| `pnpm build` | Build packages then all apps |
| `pnpm lint` | Lint all packages and apps |
| `pnpm typecheck` | Type-check all packages and apps |
| `pnpm format` | Format all files with Prettier |
| `pnpm db:generate` | Regenerate the Prisma client |
| `pnpm db:migrate` | Create and apply a migration |
| `pnpm db:studio` | Open Prisma Studio |

Run against a single workspace:
```bash
pnpm --filter @project-name/web dev
pnpm --filter @project-name/marketing build
```

## Environment Variables

### `apps/web/.env`

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `AUTH_SECRET` | Yes | Random secret — `openssl rand -base64 32` |
| `AUTH_GITHUB_ID` | Yes | GitHub OAuth client ID |
| `AUTH_GITHUB_SECRET` | Yes | GitHub OAuth client secret |
| `AUTH_GOOGLE_ID` | Yes | Google OAuth client ID |
| `AUTH_GOOGLE_SECRET` | Yes | Google OAuth client secret |
| `NEXT_PUBLIC_APP_URL` | Yes | Public URL of the web app |

### `apps/marketing/.env`

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SITE_URL` | Yes | Canonical URL for metadata |

## Package Scope

All packages use the `@project-name/` scope. Replace `@company` with your organization name across:
- `packages/*/package.json` (`name` field)
- `apps/*/package.json` (dependency references)
- Import statements throughout the codebase

```bash
# Quick rename example (adjust the pattern to your org name)
grep -rl '@project-name/' . --include='*.json' --include='*.ts' --include='*.tsx' \
  | xargs sed -i '' 's/@company\//@myorg\//g'
```

## Adding a Shared Component

```tsx
// packages/ui/src/components/badge.tsx
export function Badge({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full bg-primary px-2 py-0.5 text-xs">{children}</span>
}

// packages/ui/src/index.ts — re-export it
export { Badge } from "./components/badge"
```

Then use it in any app:
```tsx
import { Badge } from "@project-name/ui"
```

## Docker

Each app has its own `Dockerfile`. Use Docker Compose for local development with Postgres:

```bash
# Start Postgres
docker compose up -d

# Build and run apps/web
docker build -t __PROJECT_NAME__-web apps/web/
docker run -p 3000:3000 --env-file apps/web/.env __PROJECT_NAME__-web
```

## CI/CD

A GitHub Actions workflow is provided at `.github/workflows/ci.yml` — all steps are commented out by default.

**To enable CI:**

1. Open `.github/workflows/ci.yml` and uncomment the entire file
2. Add the required secrets to your GitHub repository under **Settings → Secrets and variables → Actions**:
   - `DATABASE_URL` — PostgreSQL connection string for the test database
   - `AUTH_SECRET` — Random string (`openssl rand -base64 32`)
   - `AUTH_GITHUB_ID` — GitHub OAuth app client ID
   - `AUTH_GITHUB_SECRET` — GitHub OAuth app client secret
   - `AUTH_GOOGLE_ID` — Google OAuth app client ID
   - `AUTH_GOOGLE_SECRET` — Google OAuth app client secret
   - `NEXT_PUBLIC_APP_URL` — Public URL (e.g. `http://localhost:3000` for CI)
3. Push to `main` or open a pull request — the workflow will run automatically

The workflow runs on every push to `main` and every pull request, covering lint, typecheck, and build.

## Security

### Rate Limiting

Rate limiting is not included in the boilerplate. To add it:

1. Install: `pnpm add @upstash/ratelimit @upstash/redis`
2. Add your Upstash Redis credentials to `.env`
3. Add a rate limit check in `proxy.ts` or individual API route handlers

See [Upstash Rate Limit docs](https://upstash.com/docs/oss/sdks/ts/ratelimit/overview) for configuration options.

## Git Hooks

[Husky](https://typicode.github.io/husky/) + [lint-staged](https://github.com/okonet/lint-staged) + [commitlint](https://commitlint.js.org/) are pre-configured at the repo root. The `prepare` script runs `husky` automatically on `pnpm install`, activating the hooks in `.husky/`.

### Pre-commit

On every `git commit`, lint-staged runs against staged files across all workspaces:

| Pattern | Commands |
|---------|----------|
| `*.{ts,tsx}` | `eslint --fix` → `prettier --write` |
| `*.{json,css,md}` | `prettier --write` |

Staged files are auto-fixed and re-staged before the commit lands. A failing lint error aborts the commit.

### Commit message format

[Conventional Commits](https://www.conventionalcommits.org/) is enforced via commitlint:

```
<type>[optional scope]: <description>

feat: add OAuth login with GitHub
fix(auth): resolve token refresh race condition
docs: update deployment instructions
chore: upgrade dependencies to latest
refactor(ui): extract Button into shared component
test: add unit tests for cart calculation
```

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code change that is not a fix or feature |
| `test` | Adding or updating tests |
| `chore` | Build, tooling, dependency updates |
| `ci` | CI/CD configuration |

A `BREAKING CHANGE:` footer or `!` after the type (e.g. `feat!:`) signals a breaking change and bumps the major version in semantic release.

### Skipping hooks (emergency only)

```bash
git commit --no-verify -m "chore: emergency hotfix"
```

Use sparingly — CI will still enforce lint and type-check on push.
