# Nexus MCP — Deep Project Analysis

> Generated: March 13, 2026 · Version analyzed: **2.3.5**

---

## Project Overview

**Nexus** is an enterprise-grade developer toolkit published on PyPI as `nexus-toolkit`. It bridges design tools (Figma Make) and production code through an LLM-powered pipeline, while also offering a full suite of SDLC automation agents.

**Two primary interfaces:**
- `nexus-mcp` — an MCP server (FastMCP) consumed by Claude Code, n8n, Claude Desktop, Cursor
- `nexus` — a Typer CLI for local/CI use

---

## Architecture

### Core Layers

```
nexus_server.py (FastMCP)
├── tools/search.py           → nexus_search, nexus_read
├── tools/figma/              → 7-tool Design-to-Code pipeline
│   ├── ingest.py             (zip / directory input)
│   ├── prompt_ingest.py      (text description input)
│   ├── codebase_ingest.py    (existing project input)
│   ├── remap.py              (golden path mapping + queue generation)
│   ├── validate.py           (26 static analysis checks)
│   ├── package.py            (reachability analysis + ZIP output)
│   └── filetree.py           (update_file_in_tree for API clients)
└── tools/devsecops/          → agent runner + memory
    ├── agent_runner.py       (run_agent, list_agents)
    └── memory.py             (persistent two-layer team memory)
```

### Agent Namespaces (3 Distinct Systems)

| Namespace | Location | Count | Trigger |
|-----------|----------|-------|---------|
| Golden Path | `tools/agents/` | 8 | `remap_to_golden_path` → queue files |
| Dev-Workflow | `tools/dev-agents/` | 22 | `run_agent` MCP / `nexus agent run` |
| Workflow Commands | `.claude/commands/` | 11 | `/workflow-*` slash commands |

### Golden Paths

| Golden Path | Stack |
|-------------|-------|
| `nextjs-fullstack` | Next.js 16.1, tRPC v11, Prisma v7, NextAuth v5, Zustand v5, Tailwind v4, shadcn/ui |
| `nextjs-static` | Next.js 16.1, React 19.2, Tailwind v4, static export |
| `t3-stack` | T3 conventions (src/ layout), tRPC + Prisma + NextAuth + Zustand, Tailwind v4 |
| `vite-spa` | Vite 6, React 19.2, Tailwind v4, React Router v7, TanStack Query |
| `monorepo` | Turborepo, apps/web + apps/marketing, shared packages/ui + packages/db |
| `full-stack-rn` | Turborepo, Next.js 16 + Supabase API web, Expo 54 bare + NativeWind mobile |
| `full-stack-flutter` | Turborepo, Next.js 16 + Supabase API web, Flutter 3.32 + Riverpod + go_router mobile |

---

## Strengths

### 1. Pipeline Design Is Clean and Well-Abstracted
The 5-stage pipeline (Ingest → Remap → Transform → Validate → Package) is a sound architecture. The queue-file mechanism — embedding the full golden path agent rules directly inside each `.md` queue file — is a particularly clever design: it makes each work unit self-contained and eliminates external file dependencies during LLM transformation.

### 2. Comprehensive 26-Check Static Validator
`tools/figma/validate.py` is production-focused. Checks include SSR browser-global guards, CSRF helper detection, audit columns in Prisma schemas, graceful shutdown detection, and `__PROJECT_DESCRIPTION__` placeholder verification — showing genuine enterprise thinking beyond just "does the code compile."

### 3. Dual-Mode `run_agent`
The `CLAUDECODE` environment variable detection in `tools/devsecops/agent_runner.py` is elegant: it returns `system_prompt + user_message` for Claude Code sessions (no subprocess), and falls back to a `claude` CLI subprocess for n8n/server callers. This single design decision avoids the entire class of subprocess timeout and session-blocking problems.

### 4. Two-Layer Agent Memory System
`tools/devsecops/memory.py` implements `shared/` (git-committed, team-wide) + `personal/` (gitignored, per-developer) memory layers with frontmatter tracking, human-in-the-loop trigger detection (keyword matching — no extra LLM calls), deduplication, and rolling windows. This is a well-thought-out persistence model for long-running agent workflows.

### 5. Golden Path Coverage
7 golden paths covering the major front-end stacks with pinned modern library versions, `manifest.json`-driven configuration, and enterprise production-readiness boilerplate (CSRF, sanitize, health endpoints, structured logging, Prisma audit columns).

### 6. Test Suite Layering
Tests are meaningfully structured across multiple layers:

| File | Focus |
|------|-------|
| `test_figma_pipeline.py` | Business logic via direct function extraction |
| `test_mcp_protocol.py` | Protocol layer via `FastMCP.call_tool()` — the real dispatch path |
| `test_memory.py` | 23 focused unit tests for memory internals |
| `test_improvements.py` | Regression tests for specific pipeline fixes |

### 7. Stateless HTTP Server Config
`stateless_http=True` and `json_response=True` in `nexus_server.py` are correct and practical — they support raw `curl` calls from n8n SSH nodes without SSE or session state handling.

---

## Issues & Areas for Improvement

### 1. Hardcoded Golden Path Guards in `validate.py` _(tracked in TODO.md)_
`tools/figma/validate.py` still contains `if golden_path == "vite-spa"` and `if golden_path == "t3-stack"` guards scattered in the code. `TODO.md` correctly identifies this as the primary refactoring target — validation rules should be manifest-driven. Until resolved, adding a new golden path requires Python changes.

**File:** `tools/figma/validate.py` lines 466, 535

### 2. Large Monolithic CLI Module
`nexus_cli.py` is a ~1300-line single module handling CLI commands, UX helpers, agent running, subprocess management, and update checks. At this size it becomes harder to maintain and test. The `_decompose_description()` function (which calls a subprocess for LLM inference) is untested.

### 3. `remap.py` Constants Not Manifest-Driven
`DISCARD_STEMS`, `ROOT_ENTRY_STEMS`, `SECTION_KEYWORDS`, and `_COMPONENT_SUFFIXES` in `tools/figma/remap.py` are hardcoded Python constants. As `TODO.md` notes, these should move into each `manifest.json`. This blocks zero-Python golden path additions.

### 4. SSRF Risk in `nexus_read`
`tools/search.py` validates that URLs start with `http://` or `https://`, but there is no allowlist or SSRF mitigation for internal network addresses (e.g., `http://169.254.169.254/...` AWS metadata endpoint). Since this is a server-side tool callable by any MCP client, this is a minor but real SSRF exposure.

### 5. `_check_update()` Lacks Explicit SSL Context
In `nexus_cli.py`, the update check uses `urllib.request.urlopen` with no explicit SSL context — it relies on the system default. For hardened environments, explicit `ssl.create_default_context()` is more robust.

### 6. Temp Directory Collisions / No Cleanup
The pipeline writes to `/tmp/nexus-{project_name}/`. There is no automatic cleanup, TTL, or collision detection. If two pipelines run simultaneously with the same `project_name` (e.g., in CI), they will corrupt each other's state. A UUID suffix or explicit locking would prevent this.

### 7. Missing CLI Test Coverage
There are no tests that exercise CLI command dispatch, the `transform` command's subprocess spawning, or the `agent run --server` HTTP mode added in v2.3.5. The CLI is largely untested beyond integration.

### 8. `_decompose_description` Has No Timeout
In `nexus_cli.py`, the `_decompose_description` `subprocess.run` call has no `timeout=` parameter. A hung `claude` CLI call would block the CLI indefinitely.

### 9. Version Hardcoded in Two Places
`_VERSION = "2.3.5"` is a string literal in `nexus_cli.py` that must be manually kept in sync with `pyproject.toml`. The server already does this correctly via `importlib.metadata.version("nexus-toolkit")` — the CLI should do the same.

---

## Dependency Assessment

| Package | Purpose | Notes |
|---------|---------|-------|
| `mcp[cli]>=1.0.0` | FastMCP server | Core, well-maintained |
| `httpx>=0.27.0` | HTTP client for `nexus_read` | Good choice, async-compatible |
| `beautifulsoup4>=4.12.0` | HTML parsing | Standard |
| `ddgs>=1.0.0` | DuckDuckGo search | Has a try/except fallback for the old `duckduckgo_search` package name |
| `typer>=0.12.0` | CLI framework | Good |
| `rich>=13.0.0` | Terminal output | Well-used throughout |

The dependency footprint is minimal and well-chosen for the project scope.

---

## Summary Ratings

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Architecture | ★★★★★ | Clean layering, self-contained queue files, dual-mode agent runner |
| Code Quality | ★★★★☆ | Good overall; CLI module is oversized |
| Test Coverage | ★★★★☆ | Protocol + unit + regression layers; CLI untested |
| Security | ★★★★☆ | Good SSRF start but no internal IP blocklist on `nexus_read` |
| Documentation | ★★★★★ | README, AGENTS_GUIDE, CHANGELOG, TODO all thorough |
| Production Readiness | ★★★★☆ | Temp dir collisions and missing cleanup are the main gap |
| Extensibility | ★★★☆☆ | Blocked by hardcoded Python constants (TODO acknowledged) |

---

## Top Recommendations (Priority Order)

1. **Complete the manifest-driven refactor** (`TODO.md` §1–4) — move `DISCARD_STEMS`, `ROOT_ENTRY_STEMS`, naming rules, and validation toggles into `manifest.json`. This is the single highest-leverage change and unlocks zero-Python golden path additions.

2. **Add SSRF protection to `nexus_read`** — block RFC-1918 (`10.x`, `172.16.x`, `192.168.x`) and link-local (`169.254.x`) addresses before making any outbound HTTP request.

3. **Add a timeout to `_decompose_description`** — `subprocess.run(..., timeout=60)` as a minimum to prevent indefinite hangs.

4. **Unify version management in `nexus_cli.py`** — replace the `_VERSION = "2.3.5"` literal with `importlib.metadata.version("nexus-toolkit")` to eliminate the manual sync requirement.

5. **Use a UUID or locking for the temp cache** — append a short UUID (or use a lock file) to `/tmp/nexus-{project_name}/` to prevent concurrent pipeline collisions in CI environments.
