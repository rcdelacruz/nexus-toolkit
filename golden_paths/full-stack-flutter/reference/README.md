# __PROJECT_NAME__

__PROJECT_DESCRIPTION__

## Apps

| App | Description |
|-----|-------------|
| `apps/web` | Next.js 16 App Router — REST API + dashboard UI (TypeScript) |
| `apps/mobile` | Flutter 3.32 — iOS & Android (Dart, Riverpod, go_router) |

## Packages

| Package | Description |
|---------|-------------|
| `packages/ui-primitives` | Design tokens (colors, spacing, typography, radius, shadows) — TypeScript constants |
| `packages/ui-web` | Web UI components — shadcn/ui + Tailwind v4 |
| `packages/shared` | Web-side business logic — types, utils, constants, Zod schemas |
| `packages/supabase` | Supabase client + DB types + RBAC + audit helpers (web only) |
| `packages/config` | Shared TypeScript + ESLint configs |

> **Note:** `apps/mobile` is a standalone Flutter/Dart project. It is NOT part of the pnpm workspace.
> Flutter manages its own dependencies via `apps/mobile/pubspec.yaml`.

## Getting Started

### Prerequisites

- Node.js 22+
- pnpm 9+
- Flutter SDK 3.32+ (`flutter doctor` to verify)
- Supabase CLI (`brew install supabase/tap/supabase`)
- Xcode (for iOS builds)
- Android Studio (for Android builds)

### 1. Install dependencies

```bash
make install
# equivalent to: pnpm install && cd apps/mobile && flutter pub get
```

### 2. Set up Supabase locally

```bash
supabase start
```

Copy the output URLs and keys into your env files.

### 3. Configure environment variables

**`apps/web/.env.local`** (copy from `.env.example`):
```
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon key from supabase start>
SUPABASE_SERVICE_ROLE_KEY=<service_role key from supabase start>
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**`apps/mobile/.env.json`** (copy from `.env.example.json`):
```json
{
  "SUPABASE_URL": "http://127.0.0.1:54321",
  "SUPABASE_ANON_KEY": "<anon key from supabase start>",
  "API_URL": "http://localhost:3000"
}
```

> Flutter uses `--dart-define-from-file` for environment variables, not `.env` files.

### 4. Apply the database schema

```bash
supabase db push --local < packages/supabase/sql/schema.sql
```

### 5. Generate TypeScript types from schema

```bash
supabase gen types typescript --local > packages/supabase/src/types/database.ts
```

### 6. Run Dart code generation (Riverpod + Freezed)

```bash
make mobile-codegen
```

### 7. Start development

```bash
# Start web (terminal 1)
pnpm dev

# Start Flutter (terminal 2)
make mobile-dev
```

## Architecture

`apps/mobile` authenticates directly with Supabase (gets a JWT), then calls `apps/web`
REST API endpoints with that JWT as a Bearer token. `apps/web` verifies the JWT server-side,
handles business logic, RBAC enforcement, and audit logging.

```
apps/mobile  →  Supabase Auth  (direct: get JWT via supabase_flutter)
apps/mobile  →  apps/web API   (Bearer JWT: data operations via http package)
apps/web     →  Supabase DB    (server-side: verified identity, RBAC, audit)
```

## Package Relationships

```
packages/ui-primitives   ← design token source (TypeScript constants; web only)
    ↓
packages/ui-web          ← shadcn/ui + Tailwind v4 (web only)
packages/shared          ← types, utils, constants (web only)
packages/supabase        ← auth, DB, RBAC, audit (web only)

apps/mobile              ← self-contained Flutter app
    └── supabase_flutter ← direct Supabase auth for Flutter
    └── go_router        ← navigation
    └── flutter_riverpod ← state management
    └── freezed          ← immutable models
```

## Mobile Production Builds

Flutter builds use the native toolchain:

```bash
# Build iOS (requires Xcode + Apple Developer account)
make mobile-build-ios

# Build Android APK
make mobile-build-android
```

## Turborepo Remote Cache

Run once to enable shared build cache across your team:

```bash
turbo login
turbo link
```

## CI/CD

A GitHub Actions workflow is provided at `.github/workflows/ci.yml` — all steps are commented out by default.

**To enable CI:**

1. Open `.github/workflows/ci.yml` and uncomment the entire file
2. Add the required secrets to your GitHub repository under **Settings → Secrets and variables → Actions**:
   - `NEXT_PUBLIC_SUPABASE_URL` — Supabase project URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase anon key
   - `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key
   - `NEXT_PUBLIC_APP_URL` — Public URL (e.g. `http://localhost:3000` for CI)
3. Push to `main` or open a pull request — the workflow will run automatically

The workflow runs on every push to `main` and every pull request, covering lint, typecheck, and build for the web app.

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
