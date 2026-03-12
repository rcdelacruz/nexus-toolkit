# __PROJECT_NAME__

__PROJECT_DESCRIPTION__

## Tech Stack

| | |
|---|---|
| Framework | Next.js 16.1 (App Router, standalone output) |
| Language | TypeScript 5 (strict) |
| Styling | Tailwind CSS v4 + shadcn/ui |
| State | Zustand v5 |
| API | tRPC v11 + TanStack Query v5 |
| Auth | NextAuth v5 (GitHub + Google OAuth) |
| ORM | Prisma v7 (PostgreSQL) |
| Testing | Vitest v3 |
| Linting | ESLint 9 + typescript-eslint |
| Formatting | Prettier 3 + prettier-plugin-tailwindcss |
| Git hooks | Husky + lint-staged + commitlint |

## Project Structure

```
src/
├── app/
│   ├── globals.css              # Tailwind v4 theme tokens + base styles
│   ├── layout.tsx               # Root layout — fonts, providers
│   ├── page.tsx                 # Home page
│   ├── (auth)/                  # Auth route group (login, register)
│   ├── (dashboard)/             # Protected route group
│   └── api/
│       ├── auth/[...nextauth]/  # NextAuth handler
│       └── trpc/[trpc]/         # tRPC HTTP handler
├── components/
│   ├── layout/                  # DashboardLayout, Sidebar, TopBar
│   └── ui/                      # shadcn/ui primitives (Button, Card, …)
├── server/
│   ├── auth.ts                  # NextAuth config
│   ├── trpc.ts                  # tRPC init, context, procedures
│   └── api/
│       ├── root.ts              # App router
│       └── routers/             # Feature routers
├── trpc/
│   ├── react.tsx                # Client-side tRPC provider
│   ├── server.ts                # Server-side caller (RSC)
│   └── query-client.ts          # TanStack Query client factory
├── lib/
│   ├── db.ts                    # Prisma client singleton
│   └── utils.ts                 # cn() helper
├── store/
│   └── useAppStore.ts           # Zustand global store
└── generated/                   # Prisma-generated client (gitignored post-generate)

prisma/
├── schema.prisma                # Database schema
└── config.ts                   # Prisma v7 config
docker-compose.yml               # Local PostgreSQL for development
```

## Getting Started

**Prerequisites:** Node.js 22+, pnpm 9+, Docker (for local Postgres)

```bash
# 1. Copy and fill in environment variables
cp .env.example .env

# 2. Install dependencies
pnpm install

# 3. Start the local database
docker compose up -d

# 4. Apply the schema and generate the Prisma client
pnpm db:migrate
pnpm db:generate

# 5. Start the development server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Available Scripts

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start dev server with Turbopack |
| `pnpm build` | Build for production |
| `pnpm start` | Start the production server |
| `pnpm lint` | Run ESLint |
| `pnpm typecheck` | Run TypeScript compiler (no emit) |
| `pnpm test` | Run Vitest |
| `pnpm test:ui` | Run Vitest with the browser UI |
| `pnpm format` | Format all files with Prettier |
| `pnpm db:push` | Push schema changes (skips migration history) |
| `pnpm db:migrate` | Create and apply a migration |
| `pnpm db:generate` | Regenerate the Prisma client |
| `pnpm db:studio` | Open Prisma Studio |

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `AUTH_SECRET` | Yes | Random secret — run `openssl rand -base64 32` |
| `AUTH_GITHUB_ID` | Yes | GitHub OAuth app client ID |
| `AUTH_GITHUB_SECRET` | Yes | GitHub OAuth app client secret |
| `AUTH_GOOGLE_ID` | Yes | Google OAuth app client ID |
| `AUTH_GOOGLE_SECRET` | Yes | Google OAuth app client secret |
| `NEXT_PUBLIC_APP_URL` | Yes | Public URL of the app (e.g. `http://localhost:3000`) |

## Adding Features

**New tRPC router:**
```ts
// src/server/api/routers/posts.ts
export const postsRouter = createTRPCRouter({
  list: publicProcedure.query(({ ctx }) => ctx.db.post.findMany()),
})
// Register in src/server/api/root.ts
```

**New Prisma model:**
```bash
# Edit prisma/schema.prisma, then:
pnpm db:migrate     # create and apply migration
pnpm db:generate    # regenerate client types
```

## Docker

```bash
# Start local Postgres only
docker compose up -d

# Full production image
docker build -t __PROJECT_NAME__ .
docker run -p 3000:3000 --env-file .env __PROJECT_NAME__
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

The workflow runs on every push to `main` and every pull request, covering lint, typecheck, test, and build.

## Security

### Rate Limiting

Rate limiting is not included in the boilerplate. To add it:

1. Install: `pnpm add @upstash/ratelimit @upstash/redis`
2. Add your Upstash Redis credentials to `.env`
3. Add a rate limit check in `proxy.ts` or individual API route handlers

See [Upstash Rate Limit docs](https://upstash.com/docs/oss/sdks/ts/ratelimit/overview) for configuration options.

## Git Hooks

[Husky](https://typicode.github.io/husky/) + [lint-staged](https://github.com/okonet/lint-staged) + [commitlint](https://commitlint.js.org/) are pre-configured. The `prepare` script runs `husky` automatically on `pnpm install`, activating the hooks in `.husky/`.

### Pre-commit

On every `git commit`, lint-staged runs against staged files:

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
