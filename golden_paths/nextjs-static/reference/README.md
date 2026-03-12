# __PROJECT_NAME__

__PROJECT_DESCRIPTION__

## Tech Stack

| | |
|---|---|
| Framework | Next.js 16.1 (App Router, `output: "export"`) |
| Language | TypeScript 5 (strict) |
| Styling | Tailwind CSS v4 (CSS-first, no config file) |
| UI Primitives | CVA + shadcn/ui component patterns |
| Icons | Lucide React |
| Font | Geist (via `next/font/google`) |
| Linting | ESLint 9 + typescript-eslint |
| Formatting | Prettier 3 + prettier-plugin-tailwindcss |
| Git hooks | Husky + lint-staged + commitlint |

## Project Structure

```
├── app/
│   ├── globals.css        # Tailwind v4 theme tokens + base styles
│   ├── layout.tsx         # Root layout — fonts, metadata
│   └── page.tsx           # Home page entry point
├── components/
│   ├── layout/            # Header, Footer
│   ├── sections/          # Page sections (Hero, Features, Pricing, CTA)
│   └── ui/                # Primitive components (Button, Card)
├── lib/
│   └── utils.ts           # cn() helper (clsx + tailwind-merge)
└── public/                # Static assets served at /
```

## Getting Started

**Prerequisites:** Node.js 22+, pnpm 9+

```bash
# 1. Install dependencies
pnpm install

# 2. Copy environment variables
cp .env.example .env.local

# 3. Start the development server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Available Scripts

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start dev server with Turbopack |
| `pnpm build` | Export static site to `out/` |
| `pnpm start` | Serve the production build locally |
| `pnpm lint` | Run ESLint |
| `pnpm typecheck` | Run TypeScript compiler (no emit) |
| `pnpm format` | Format all files with Prettier |

## Environment Variables

Copy `.env.example` to `.env.local` and fill in:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SITE_URL` | Canonical URL (used in metadata and OG tags) |
| `NEXT_PUBLIC_SITE_NAME` | Site display name |

## Build & Deploy

```bash
pnpm build
# Static output is written to out/
```

Deploy the contents of `out/` to any static host:

| Platform | Configuration |
|----------|---------------|
| Vercel / Netlify | Build command: `pnpm build` · Publish dir: `out/` |
| Cloudflare Pages | Same as above |
| Nginx | Serve `out/` as web root; configure `try_files $uri $uri/ /index.html` |
| S3 + CloudFront | Sync `out/`; set index document to `index.html` |
| GitHub Pages | Push `out/` to `gh-pages` branch |

## Docker

```bash
# Build
docker build -t __PROJECT_NAME__ .

# Run
docker run -p 3000:3000 __PROJECT_NAME__
```

```bash
# Or with Docker Compose
docker compose up
```

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
