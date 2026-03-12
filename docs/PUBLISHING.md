# Publishing & Deployment Guide

## Overview

| What | Where |
|------|-------|
| PyPI package | `nexus-toolkit` |
| Landing page | https://nexus.coderstudio.co |
| Install script | https://nexus.coderstudio.co/install.sh |
| GitHub repo | https://github.com/rcdelacruz/nexus-mcp |

---

## Install (for end users)

```bash
curl -fsSL https://nexus.coderstudio.co/install.sh | bash
```

Pin to a specific version:
```bash
NEXUS_VERSION=2.1.0 curl -fsSL https://nexus.coderstudio.co/install.sh | bash
```

---

## PyPI Setup

### Package name
`nexus-toolkit` — registered at https://pypi.org/project/nexus-toolkit/

### Trusted Publisher (one-time setup, already done)
Uses GitHub OIDC — no API token needed.

Configured at: **pypi.org → nexus-toolkit → Publishing → Trusted Publishers**

| Field | Value |
|-------|-------|
| Owner | `rcdelacruz` |
| Repository | `nexus-mcp` |
| Workflow name | `publish.yml` |
| Environment | `pypi` |

GitHub environment also created: **rcdelacruz/nexus-mcp → Settings → Environments → `pypi`**

### Publishing a new version

1. Bump `version` in `pyproject.toml`
2. Push to `main`
3. GitHub Action (`.github/workflows/publish.yml`) triggers automatically and publishes to PyPI

That's it. No manual steps needed after initial setup.

---

## Cloudflare Pages Setup

### Project details

| Field | Value |
|-------|-------|
| Project name | `nexus-coderstudio` |
| Pages URL | https://nexus-coderstudio.pages.dev |
| Custom domain | https://nexus.coderstudio.co |
| Account ID | `cf535d76fffdb44d43f6a3c00a3ebbe6` |
| Output directory | `public/` |
| Build command | *(none)* |

### Redeploy after changes to `public/`

```bash
wrangler pages deploy public/ --project-name nexus-coderstudio --branch main
```

---

## Release Checklist

Every version bump requires all of the following steps in order:

- [ ] Update `CHANGELOG.md` — add `## [X.Y.Z] — YYYY-MM-DD` at the top
- [ ] Bump version in **all 4 files**: `pyproject.toml`, `nexus_cli.py`, `public/index.html`, `public/docs.html`
- [ ] Commit and push to `main` → GitHub Action auto-publishes to PyPI (triggered by `pyproject.toml` change)
- [ ] Tag and create GitHub release:
  ```bash
  git tag vX.Y.Z && git push origin vX.Y.Z
  gh release create vX.Y.Z --title "vX.Y.Z — <description>" --latest --notes "..."
  ```
- [ ] Deploy to Cloudflare Pages (**no auto-deploy — always manual**):
  ```bash
  wrangler pages deploy public/ --project-name nexus-coderstudio --branch main
  ```
- [ ] Reinstall on server (**only if Python files changed** — `tools/**/*.py`, `nexus_server.py`, `nexus_cli.py`):
  ```bash
  # SSH as ronald@168.138.191.197
  $HOME/.local/bin/uvx --reinstall nexus-toolkit && systemctl --user restart nexus-sse
  ```
- [ ] Verify: `pip install --upgrade nexus-toolkit` installs new version
- [ ] Verify: `curl -fsSL https://nexus.coderstudio.co/install.sh | bash` works
