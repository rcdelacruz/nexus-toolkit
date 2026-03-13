# Changelog

All notable changes to this project are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions correspond to the `nexus-toolkit` PyPI package.

---

## [2.3.3] — 2026-03-13

### Fixed
- **`run_agent` dual-mode**: detects `CLAUDECODE` env var — returns prompt-return for Claude Code sessions, runs subprocess for n8n/server (no `CLAUDECODE`)

---

## [2.3.2] — 2026-03-13

### Changed
- **`run_agent` MCP tool** — no longer spawns a claude CLI subprocess; instead returns `system_prompt` + `user_message` for the current Claude Code session to apply directly, eliminating all timeout issues

---

## [2.3.1] — 2026-03-13

### Added
- **`get_version` MCP tool** — MCP clients can now query the running `nexus-toolkit` version at runtime via `get_version()`

### Fixed
- **`run_agent` idle timeout** — replaced hard 300s wall-clock timeout with a 240s idle timeout; active LLM generation resets the timer so long-running agents (e.g. `product-manager`) are never killed prematurely

---

## [2.3.0] — 2026-03-13

### Added
- **Persistent agent memory** (`tools/devsecops/memory.py`) — file-based markdown memory for dev-workflow agents with two-layer team model:
  - `personal/` (gitignored, per-developer) and `shared/` (git-committed, team-owned via PRs)
  - Solo projects: flat `{memory_dir}/{agent_name}.md` (auto-detected)
  - Auto-writes gitignore entry for `personal/` on first use — zero manual setup
- **`run_agent` MCP tool** — new `memory_path` and `remember` parameters; past findings are injected as context before each run; findings are written back after run when `remember=True`
- **`get_agent_memory` MCP tool** — reads the memory file for a named agent; returns merged shared + personal content
- **`update_agent_memory` MCP tool** — writes or merges findings into agent memory; supports `append` (default), `replace`, and `reset` modes
- **`nexus agent run`** CLI — new `--memory-path` and `--remember` flags; auto-detects project root when `--remember` is used without `--memory-path`
- **Human-in-the-loop trigger detection** — deterministic keyword matching (no extra LLM calls) flags major decisions (migrate, breaking change, rewrite, deprecate, etc.) as `- [ ]` checkboxes in `⚠️ Pending Human Review`; ticking `- [x]` prevents re-flagging on future runs
- **`tests/test_memory.py`** — 23 unit tests covering frontmatter parsing, trigger detection, deduplication, rolling window, mode behaviours, two-layer merge, and auto-gitignore

### Fixed
- **uvx entry point** — corrected all installation and update commands from `uvx nexus-toolkit` (which fails — no executable by that name) to `uvx --from nexus-toolkit nexus-mcp`. Affects Claude Code, Claude Desktop, Cursor, and n8n HTTP server setup instructions in README and docs.

### Changed
- `nexus_cli.py` version → 2.3.0; `public/index.html` and `public/docs.html` version badge → v2.3.0
- `public/docs.html` — new **Agent Memory** section and **Updating** section; all uvx commands corrected

---

## [2.2.0] — 2026-03-12

### Added
- **22 dev-workflow agents** across four categories: `cross-cutting` (11), `architecture` (3), `javascript` (4), `savants` (4) — covering code review, security, QA, deployment, monitoring, architecture, and language-specific development
- **`run_agent` MCP tool** — run any named dev-workflow agent against a file, diff, or inline context via `claude` CLI subprocess; optional `workflow=` parameter chains a workflow command with the agent system prompt
- **`list_agents` MCP tool** — returns all available agents grouped by category as JSON
- **`nexus agent list`** CLI command — lists all 22 agents in a Rich table grouped by category
- **`nexus agent run <name> [file]`** CLI command — runs a named agent against a file, stdin (`-`), or `--context`; supports `--model` and `--claude-path` flags
- **`nexus workflow run <name> [file]`** CLI command — runs a multi-step workflow command; same input modes as `agent run`
- **11 workflow commands** in `.claude/commands/`: `workflow-review-code`, `workflow-review-security`, `workflow-review-performance`, `workflow-deploy`, `workflow-design-architecture`, `workflow-design-nextjs`, `workflow-implement-backend`, `workflow-implement-frontend`, `workflow-implement-fullstack`, `workflow-qa-e2e`, `workflow-write-docs`
- **7 n8n DevSecOps workflows** in `n8n-workflow/`: `ds1-code-review`, `ds2-security-scan`, `ds3-db-review`, `ds4-qa-gate`, `ds5-deploy-review`, `ds6-weekly-audit`, `ds7-health-check` — each wires a CI/CD event (PR webhook, merge trigger, cron) through Auth Guard to `run_agent` via base64-encoded SSH curl
- **`AGENTS_GUIDE.md`** — architecture and data flow documentation for all three agent systems (golden path, dev-workflow, n8n DevSecOps) with mermaid diagrams

### Changed
- `pyproject.toml` package-data now includes `tools/dev-agents/**/*.md` so agent markdown files are bundled in the PyPI package
- `nexus_server.py` registers `register_devsecops_tools(mcp)` alongside the existing figma and search tool registrations
- `docs/index.html` and `docs/docs.html` updated to represent the full toolkit (Design-to-Code + Dev Agents + Workflow Commands), not only Figma tooling

---

## [2.1.5] — 2026-03-07

### Added
- **Enterprise production readiness** across all 7 golden paths in three phases:
  - Phase 1: audit columns (`deletedAt`, `createdById`) in all Prisma schemas; `validate_output` check 21 enforces these
  - Phase 2: security hardening — `lib/csrf.ts`, `lib/sanitize.ts`, `/api/health` endpoint, `next.config.ts` CSP headers — added to all server golden paths; checks 22–25 in `validate_output`
  - Phase 3: OPS hardening — `instrumentation.ts` with SIGTERM/SIGINT graceful shutdown, Prometheus metrics endpoint, structured logging — added to all server golden paths; check 23 in `validate_output`
- `__PROJECT_DESCRIPTION__` placeholder in all golden path `README.md` files — resolved from manifest description at remap time; validate check 26 flags if unresolved
- `DB_POOL_MAX` environment variable for configuring `pg.Pool` size in server golden paths

### Fixed
- TypeScript `--noEmit` errors across `nextjs-fullstack`, `t3-stack`, and `monorepo` boilerplate
- CSP headers now allow `https:` image sources and include `remotePatterns` in `next.config.ts`
- `next-auth` downgraded from v5 beta to v4.24.13 stable — v5 has no stable release and breaks session handling
- Shadcn passthrough files now always land in `{src_dir}components/ui/` regardless of component classification — fixes broken imports when Figma exports shadcn primitives that get misclassified as sections
- Agent no longer imports reference boilerplate stubs (`Features.tsx`, `CTA.tsx`, etc.) into generated pages — queue files now embed a `**Project components:**` guard list
- `validate_output` false-positive warnings removed for `generated/`, `tests/`, `instrumentation.ts`, and `seed.ts` (CONSOLE_LOG exempt; instrumentation exempt from UNCONVERTED_IMPORT)
- Phase 1/2 utility files (`lib/csrf.ts`, `lib/sanitize.ts`, etc.) exempt from orphan removal in `package_output`
- Supabase local dev URL restored in `full-stack-rn` and `full-stack-flutter` `.env.example`

---

## [2.1.2] — 2026-02-28

### Added
- `nexus update` command — upgrades `nexus-toolkit` to the latest PyPI version in-place
- `nexus version` and `nexus -v` — print current version
- Version update check on CLI startup — warns when a newer PyPI release is available

### Fixed
- `--add-dir` flag consuming the prompt argument in `_run_pipeline`; pipeline now correctly separates prompt from directory flags
- `nexus transform` now places `--prompt` before `--add-dir` in the claude CLI invocation

---

## [2.1.0] — 2026-02-20

### Added
- **`nexus` CLI** (`nexus_cli.py`) — full pipeline from the terminal with no MCP client required:
  - `nexus run zip / prompt / codebase` — one-liner full pipeline
  - `nexus ingest / remap / transform / validate / package` — individual pipeline steps
  - Rich terminal UI with step progress, timing, and error messages
  - `--model`, `--claude-path`, `--golden-path`, `--project-name`, `--output-dir`, `--prompt` flags
  - `CLAUDE_PATH` environment variable support
- **PyPI package** `nexus-toolkit` — installable via `pip install nexus-toolkit` or `uv tool install nexus-toolkit`
- **Install script** at `nexus.coderstudio.co/install.sh` — one-liner install with `uv` or `pip` fallback; clears shell hash cache after install
- **Landing page** (`public/index.html`) and **docs page** (`public/docs.html`) deployed to Cloudflare Pages at `nexus.coderstudio.co`
- **`ingest_from_prompt` LLM decomposition** — `nexus ingest prompt` now calls Claude via SSH to decompose the description into pages and components before ingesting (replaces keyword matching)

### Changed
- Package renamed from `nexus-mcp` to `nexus-toolkit` on PyPI
- MCP server and CLI share the same codebase; `nexus_server.py` is the MCP entry point, `nexus_cli.py` is the CLI entry point

---

## [2.0.0] — 2026-02-10

### Added
- **`full-stack-flutter` golden path** — Turborepo monorepo with Next.js 16 web (Supabase API) + Flutter 3.32 mobile (Riverpod + go_router); renamed from `flutter-nextjs`
- **`full-stack-rn` golden path** — Turborepo monorepo with Next.js 16 web + Expo 54 mobile (NativeWind); includes `ui-mobile` `cn()` utility
- **Enterprise boilerplate** across all 7 golden paths — production-grade `README.md`, tooling config, `.husky/` pre-commit hooks, `CONTRIBUTING.md`
- **`validate_output` checks** — `UNSAFE_BROWSER_GLOBALS` (localStorage/sessionStorage without SSR guards) and `CONSOLE_LOG` (production console calls)
- **`.claude/agents/` symlinks** — each golden path agent markdown file linked for use as Claude Code subagents
- n8n workflow sync — all 26 `ai-workflow` tagged workflows exported to `n8n-workflow/`

### Fixed
- `validate_output`: config files (`proxy`, `instrumentation`) exempted from broken-import checks
- `validate_output`: stale vs truly-unprocessed queue files distinguished correctly
- `package_output`: `.husky/` hooks preserved in output ZIP
- `remap_to_golden_path`: component path classification fixed for `nextjs-static`
- tRPC `onError` handler: removed `console.error` to pass CONSOLE_LOG validation
- Monorepo: hardcoded `@company/` scope replaced with `@project-name/` placeholder
- Page routing: `HomePage`, `home`, `index`, `landing` stems now correctly route to `app/page.tsx`

---

## [1.4.0] — 2026-01-25

### Added
- **Validate → fix → retry loop** in n8n (max 3 attempts) — failed validation triggers a fix prompt via SSH claude, re-validates automatically
- **`update_file_in_tree` MCP tool** — allows headless clients (n8n) to write transformed file content back into the cached file tree without filesystem access
- **GitHub push** via Git Trees API after successful pipeline run — replaces S3 upload
- **Orphan file stripping** in `package_output` — unreachable files excluded from ZIP; `reference_paths` tracked separately
- **Golden path agent rules embedded in queue files** — each `05_queue/*.md` file is self-contained; agent needs no external file read during transformation

### Fixed
- MCP server: `stateless_http=True` + `json_response=True` — required for n8n raw curl (no SSE handshake needed)
- MCP server: `MCP_HOST`/`MCP_PORT` environment variables take precedence over `FASTMCP_HOST`/`FASTMCP_PORT`
- n8n: base64-encoded payloads to avoid shell escaping issues across SSH
- n8n: `--system-prompt` flag for golden path and nexus-validator agents in transform and fix steps
- `remap_to_golden_path`: slim response — removed inline queue content to prevent context overflow

---

## [1.3.0] — 2026-01-15

### Added
- **n8n workflow** for automated Nexus pipeline — webhook trigger → ingest → remap → transform (SSH claude) → validate → package → push
- **`MCP_TRANSPORT`** environment variable — selects `stdio`, `sse`, or `http` transport without code changes
- **`nexus-validator` agent** (`tools/agents/nexus-validator.md`) — specialized agent for fixing validation errors in the retry loop

### Changed
- `validate_output` and `package_output` read `04_file_tree.json` directly from disk — only `_nexus_cache` path needed in tool calls

---

## [1.2.0] — 2026-01-05

### Added
- **`ingest_from_codebase` MCP tool** — ingests an existing project for migration to a golden path; skips `node_modules`, `.next`, `dist`, build output
- **`ingest_from_prompt` MCP tool** — generates a pipeline manifest from a natural language description; supports explicit `pages` and `components` lists
- **`monorepo` golden path** — Turborepo with `apps/web` + `apps/marketing`, shared `packages/ui` + `packages/db`
- **`vite-spa` golden path** — Vite 6, React 19, Tailwind v4, React Router v7, TanStack Query
- Section classification improvements — `SECTION_KEYWORDS` expanded; `Page` suffix detected before section keywords

### Fixed
- Sole page promotion — exactly one page always promoted to `app/page.tsx` regardless of name
- `validate_output`: improved config file detection; more infrastructure files excluded from import checks

---

## [1.1.0] — 2025-12-20

### Added
- **`t3-stack` golden path** — T3 conventions with tRPC v11, Prisma v7, NextAuth v4, Zustand v5, Tailwind v4
- **`nextjs-static` golden path** — Next.js static export, no server runtime
- Shadcn/ui passthrough detection — components importing `@radix-ui`, `cmdk`, `vaul`, etc. are passed through with normalized imports and enforced lowercase filenames
- `__PROJECT_NAME__`, `__PROJECT_TITLE__`, `__PROJECT_DESCRIPTION__`, `__YEAR__`, `@project-name/` placeholder substitution in reference boilerplate files
- Infrastructure content filtering (Figma source only) — files importing `prisma`, `trpc`, `next-auth`, `drizzle` marked non-design and excluded from LLM queue

---

## [1.0.0] — 2025-12-10

### Added
- **Core Design-to-Code pipeline** — `ingest_figma_zip` → `remap_to_golden_path` → `validate_output` → `package_output`
- **`nextjs-fullstack` golden path** — Next.js 16, React 19, Tailwind v4, tRPC v11, Prisma v7, NextAuth v4, Zustand v5
- **`nexus_search` MCP tool** — hybrid web search via DuckDuckGo; `general` and `docs` modes
- **`nexus_read` MCP tool** — URL content extraction; `general`, `code`, and `auto` focus modes
- FastMCP server with `stdio`, `sse`, and `http` transports
- File classification pipeline: ROOT_ENTRY_STEMS → DISCARD_STEMS → page suffix → SECTION_KEYWORDS → manifest signals → fallback ui
- `/tmp/nexus-{project}/` cache pattern — `01_manifest.json`, `04_file_tree.json`, `05_queue/` work directory
- `manifest.json` as configuration language — controls classification, tailwind version, required files, placeholder targets, conditional feature inclusion
- 13 initial validation checks — broken imports, Figma artifacts (`React.FC`, bare `import React`, inline styles), missing `"use client"`, oklch colors, tailwind config references
