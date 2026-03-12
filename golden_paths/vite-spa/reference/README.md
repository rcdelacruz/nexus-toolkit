# __PROJECT_NAME__

__PROJECT_DESCRIPTION__

## Tech Stack

| | |
|---|---|
| Bundler | Vite 6 |
| Language | TypeScript 5 (strict) |
| Routing | React Router v7 |
| Server State | TanStack Query v5 |
| UI State | Zustand v5 |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite` plugin) |
| UI Primitives | CVA + shadcn/ui component patterns |
| Icons | Lucide React |
| Notifications | Sonner |
| Linting | ESLint 9 + typescript-eslint |
| Formatting | Prettier 3 + prettier-plugin-tailwindcss |
| Git hooks | Husky + lint-staged + commitlint |

## Project Structure

```
src/
├── components/
│   ├── layout/            # Header, shell components
│   └── ui/                # Primitive components (Button, Card, …)
├── lib/
│   ├── api.ts             # TanStack Query client + typed fetch helper
│   └── utils.ts           # cn() helper (clsx + tailwind-merge)
├── routes/
│   ├── index.tsx          # Router definition
│   ├── Root.tsx           # Root route (layout shell)
│   └── pages/             # Page-level route components
│       ├── HomePage.tsx
│       ├── DashboardPage.tsx
│       └── NotFoundPage.tsx
├── store/
│   └── useAppStore.ts     # Zustand global store
├── styles/
│   └── globals.css        # Tailwind v4 theme tokens + base styles
└── main.tsx               # Application entry point
index.html                 # HTML entry point
vite.config.ts             # Vite configuration
nginx.conf                 # Production Nginx config
```

## Getting Started

**Prerequisites:** Node.js 22+, pnpm 9+

```bash
# 1. Install dependencies
pnpm install

# 2. Copy environment variables
cp .env.example .env

# 3. Start the development server
pnpm dev
```

Open [http://localhost:5173](http://localhost:5173).

## Available Scripts

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start the Vite dev server |
| `pnpm build` | Type-check and bundle for production |
| `pnpm preview` | Serve the production build locally |
| `pnpm lint` | Run ESLint |
| `pnpm typecheck` | Run TypeScript compiler (no emit) |
| `pnpm format` | Format all files with Prettier |

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Base URL of the backend API (e.g. `http://localhost:8080`) |

All client-side env vars must be prefixed with `VITE_` and accessed via `import.meta.env.VITE_*`.

## Adding a Route

```tsx
// src/routes/pages/ProfilePage.tsx
export function ProfilePage() {
  return <div>Profile</div>
}

// src/routes/index.tsx — add to the router
{ path: "profile", element: <ProfilePage /> }
```

## Build & Deploy

```bash
pnpm build
# Output is in dist/
```

**Nginx** (included `nginx.conf`):
```bash
# Copy dist/ to your server and point Nginx at it
# nginx.conf handles SPA fallback (all paths → index.html)
```

**Docker:**
```bash
docker build -t __PROJECT_NAME__ .
docker run -p 80:80 __PROJECT_NAME__
```

**Vercel / Netlify:** connect your repository — build command `pnpm build`, publish directory `dist/`. Configure SPA rewrite (all paths → `index.html`).

## CI/CD

A GitHub Actions workflow is provided at `.github/workflows/ci.yml` — all steps are commented out by default.

**To enable CI:**

1. Open `.github/workflows/ci.yml` and uncomment the entire file
2. No secrets are required for this workflow — lint, typecheck, and build run without them
3. Push to `main` or open a pull request — the workflow will run automatically

The workflow runs on every push to `main` and every pull request, covering lint, typecheck, and build.

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
