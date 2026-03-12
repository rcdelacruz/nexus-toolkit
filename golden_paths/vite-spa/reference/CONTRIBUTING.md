# Contributing

## Development setup

Follow the **Getting Started** steps in [README.md](README.md).

## Branch naming

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code — never commit directly |
| `feat/<slug>` | New feature |
| `fix/<slug>` | Bug fix |
| `chore/<slug>` | Tooling, dependency updates |
| `docs/<slug>` | Documentation only |
| `refactor/<slug>` | Code refactoring without behaviour change |

## Workflow

1. Create a branch from `main`: `git checkout -b feat/my-feature`
2. Make your changes — keep commits small and focused
3. Push your branch and open a pull request against `main`
4. At least one approval required before merging
5. Squash-merge to keep history clean

## Commit messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Commitlint enforces the format on every commit.

```
feat: add OAuth login with GitHub
fix(auth): resolve token refresh race condition
docs: update deployment instructions
chore: upgrade dependencies to latest
```

## Code quality

Before pushing, ensure:

```bash
pnpm lint        # ESLint — must pass with zero errors
pnpm typecheck   # TypeScript — must pass with zero errors
pnpm format      # Prettier — auto-formats, then commit any changes
```

All of these run automatically in CI on every pull request.

## Pull request checklist

- [ ] Branch is up to date with `main`
- [ ] `pnpm lint` passes
- [ ] `pnpm typecheck` passes
- [ ] Tests pass (if applicable)
- [ ] New behaviour is covered by tests
- [ ] PR description explains **why**, not just **what**
