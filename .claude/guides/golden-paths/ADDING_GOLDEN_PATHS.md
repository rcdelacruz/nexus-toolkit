# Adding a New Golden Path

This guide is for engineers who want to add a new golden path to the Nexus MCP pipeline — whether it's another TypeScript/React variant, a completely different framework (Vue, Svelte, Angular), or a different language ecosystem (Python/Django, Ruby on Rails, Go, etc.).

---

## How the Pipeline Uses a Golden Path

Understanding the data flow first makes the checklist obvious.

```
ingest_figma_zip
  └─ reads: golden_paths/{name}/          ← does this directory exist?

remap_to_golden_path
  ├─ reads: golden_paths/{name}/manifest.json   ← routing, classification, required files
  ├─ seeds: golden_paths/{name}/reference/      ← boilerplate copied into output tree
  ├─ classifies Figma files using manifest classification rules
  ├─ auto-passes shadcn/ui primitives (React/TS only — see §Language Extensions)
  └─ writes: 05_queue/{n}_ComponentName.md
       └─ each queue file says: "Follow .claude/agents/{name}.md rules"

golden path agent (.claude/agents/{name}.md)
  └─ transforms Figma source → production code following the agent's rules

validate_output
  ├─ reads: golden_paths/{name}/manifest.json   ← requiredFiles check
  └─ runs static checks, some of which are golden-path-specific

package_output
  └─ zips the file tree — no golden path awareness needed
```

**Key insight**: `ingest.py` discovers valid golden paths by scanning `golden_paths/` for subdirectories. There is no hardcoded list — adding the directory is enough for the pipeline to accept it as a valid `golden_path` parameter.

---

## The Six Artifacts (Required for Every Golden Path)

### 1. `golden_paths/{name}/reference/` — the boilerplate

The seed project. Every file here is copied verbatim into the output file tree before the LLM works on it. The LLM fills in the Figma-derived components on top of this foundation.

**Minimum contents for a TypeScript/React golden path:**

```
reference/
  package.json             ← use ^ ranges; keep versions consistent with other paths
  tsconfig.json
  next.config.ts           ← or vite.config.ts / equivalent
  .gitignore               ← include node_modules/, generated/, build dirs
  .env.example
  eslint.config.mjs
  .prettierrc
  postcss.config.mjs       ← Next.js only (needed for @tailwindcss/postcss)
  Dockerfile
  docker-compose.yml
  README.md
  app/layout.tsx           ← App Router entry; or src/main.tsx for Vite
  app/globals.css          ← Tailwind v4 token structure
  components/ui/           ← shadcn/ui primitives (lowercase filenames)
  lib/utils.ts             ← cn() helper
  lib/db.ts                ← if using Prisma
  server/trpc.ts           ← if using tRPC
  server/api/root.ts       ← if using tRPC (must have at least one procedure — see §Known Gotchas)
  server/api/routers/example.ts  ← the required "dummy" procedure
  .nvmrc                       ← Node version pin (e.g. "22")
  LICENSE                      ← MIT with __YEAR__ and __AUTHOR__ placeholders
  CHANGELOG.md                 ← Keep a Changelog stub
  CONTRIBUTING.md              ← Branch naming, workflow, commit format, code quality
  .github/dependabot.yml       ← Automated dependency updates (npm, weekly)
  .github/PULL_REQUEST_TEMPLATE.md
  .github/ISSUE_TEMPLATE/bug_report.md
  .github/ISSUE_TEMPLATE/feature_request.md
  .github/workflows/ci.yml     ← CI workflow — all steps commented out by default
```

**CI workflow**: `.github/workflows/ci.yml` ships fully commented out. Developers uncomment it after configuring repository secrets. This prevents broken pipelines on fresh clones before secrets are set.

**LICENSE placeholders**: `__YEAR__` is substituted at generation time by `remap.py`. `__AUTHOR__` is left as a manual fill-in — the developer replaces it after cloning.

**Non-TypeScript golden path** — contents depend entirely on the stack. See §Language Extensions.

**Validation:** Run the project's typecheck / lint before committing:
```bash
# TypeScript
pnpm install --ignore-scripts && pnpm typecheck

# Python
uv sync && mypy .

# Ruby
bundle install && bundle exec srb tc
```
Zero errors required before the reference is committed.

---

### 2. `golden_paths/{name}/manifest.json` — pipeline metadata

This JSON file controls how `remap_to_golden_path` handles the golden path. All fields are read at pipeline time.

```jsonc
{
  "name": "your-path-name",
  "version": "1.0.0",
  "description": "One-line description of what this stack is",

  "routing": {
    // "strategy" is informational only — used by the agent prompt, not by Python code
    "strategy": "app-router",          // or "file-based", "explicit", etc.

    // srcDir is the ONLY routing field the Python pipeline reads.
    // It prefixes all auto-generated component output paths.
    // Use "" for root-level layouts (nextjs-*), "src/" for T3/Vite-style.
    "srcDir": "",

    // Informational flags — passed to the agent via queue file context
    "asyncParams": true,
    "staticExport": false
  },

  "tailwind": {
    // version is informational — tells the agent which Tailwind API to use
    "version": 4,
    "configFile": null,                // null = no tailwind.config.ts (v4)
    "cssFile": "app/globals.css",      // path to the token file; used by validate_output
    "tokenDirective": "@theme inline",
    "animatePackage": "tw-animate-css"
  },

  // CSS/token files the agent must populate with Figma design tokens.
  // Used to write targeted instructions in queue files.
  "tokenTargets": ["app/globals.css"],

  // validate_output checks that every path in this list exists in the output tree.
  // Keep this list to files that are always required, not optional ones.
  "requiredFiles": [
    "app/layout.tsx",
    "app/globals.css",
    "lib/utils.ts",
    "package.json",
    "tsconfig.json",
    "next.config.ts",
    ".env.example",
    "Dockerfile",
    "docker-compose.yml",
    "README.md",
    "eslint.config.mjs",
    ".prettierrc",
    "postcss.config.mjs",
    ".nvmrc",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    ".github/dependabot.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/workflows/ci.yml"
  ],

  // classification tells remap_to_golden_path where to write each Figma component.
  // The {ComponentName} placeholder is replaced with the actual component stem.
  // signals is a keyword list — if the stem contains any signal word (case-insensitive),
  // the file gets classified into that category.
  "classification": {
    "categories": {
      "layout": {
        "outputPath": "components/layout/{ComponentName}.tsx",
        "signals": ["Header", "Footer", "Navigation", "Navbar", "Sidebar", "TopBar", "Shell"]
      },
      "section": {
        "outputPath": "components/sections/{ComponentName}.tsx",
        "signals": ["Hero", "Features", "Pricing", "Testimonials", "CTA", "FAQ", "About", "Team", "Banner"]
      },
      "ui": {
        "outputPath": "components/ui/{ComponentName}.tsx",
        "signals": ["Button", "Card", "Badge", "Input", "Label", "Avatar", "Toast", "Skeleton"]
      }
    }
  }
}
```

**For non-React golden paths** — the `classification.categories.outputPath` templates are what changes. Examples:

```jsonc
// Vue SPA
"layout": { "outputPath": "src/components/layout/{ComponentName}.vue" }
"ui":     { "outputPath": "src/components/ui/{ComponentName}.vue" }

// Django
"template": { "outputPath": "templates/{component_name}.html" }
"view":     { "outputPath": "{app_name}/views/{component_name}.py" }
```

The `{ComponentName}` token is always replaced with the Figma file's stem (PascalCase). Any other tokens like `{component_name}` or `{app_name}` require a code change in `remap.py:_resolve_output_path()` — see §Language Extensions.

---

### 3. `.claude/agents/{name}.md` — the LLM transformation agent

The agent that Claude Code spawns (via the `Task` tool) to rewrite each Figma component into your stack's conventions.

**Required frontmatter:**
```markdown
---
name: your-path-name
description: Use this agent to apply golden path convention fixes to pre-processed Figma Make source files for [name] projects. Invoke during Nexus pipeline step 5 when golden_path is [name].
---
```

The description is used by Claude Code's agent selector — it must say "Invoke during Nexus pipeline step 5 when golden_path is [name]."

**Required sections** (adapt content for your stack):

| Section | Purpose |
|---------|---------|
| Two non-negotiable laws | Figma fidelity + golden path structure |
| Design Extraction | What to extract before writing code |
| Stack (Non-Negotiable) | Table of technologies + versions — must match `reference/package.json` |
| TypeScript/Language Rules | Type safety rules for your language |
| Component Architecture Rules | File conventions, export style, etc. |
| Framework-specific rules | e.g. Next.js rules, Vite rules, Django rules |
| Tailwind/CSS/Styling Rules | Color token rules, animation package |
| Import Rules | Path aliases, import grouping |
| Accessibility Rules | Semantic HTML, aria, focus |
| Security Rules | Input validation, secrets handling |
| Code Cleanliness Rules | No console.log, no dead code, etc. |
| What You Must NEVER Do | Hard prohibitions as a flat list |
| Mandatory Self-Review | Per-file checklist |
| Your Workflow | Step-by-step: read queue → extract → write → self-review → update tree → delete queue file |

The Stack table version numbers **must stay in sync** with `reference/package.json`. See `MAINTENANCE.md` for the two-sources-of-truth rule.

---

### 4. `pnpm typecheck` (or equivalent) passes with zero errors

Before committing, install and verify the reference boilerplate compiles cleanly. This is non-negotiable — a broken boilerplate produces broken output on every single run.

```bash
cd golden_paths/{name}/reference
pnpm install --ignore-scripts
pnpm typecheck
```

---

### 5. Update `MAINTENANCE.md`

Add the new path to:
- The **Two Sources of Truth** table
- The **Quarterly Sweep Process** section (any path-specific commands, e.g. `db:generate`)
- The **Known Breaking Patterns** section if your stack has any at the time of creation
- The **File Checklist for a New Golden Path** — confirm you ticked every item

---

### 6. Update `GOLDEN_PATH_GUIDE.md`

Add the new path to:
- The **Quick-Select Table** (one-line description)
- A full **Golden Path Profile** section (Best for / What it gives you / When to choose / When NOT to choose)
- The **Deployment Compatibility** table
- The **Complexity vs Capability** chart

---

## Known Gotchas (TypeScript/React Paths)

These are lessons already learned. Check `MAINTENANCE.md §Known Breaking Patterns` for the current full list.

### tRPC v11 RSC — empty router breaks `createHydrationHelpers`

`createHydrationHelpers<typeof appRouter>` uses the conditional type:
```
AnyRouter extends TRouter ? TypeError<"Generic parameter missing..."> : Caller<TRouter>
```
When `appRouter = createTRPCRouter({})` (empty `{}`), `AnyRouter extends Router<TRoot, {}>` evaluates to `true` because `Router<any, any>` is structurally compatible via `any`. The type resolves to a `TypeError` instead of a usable caller.

**Fix**: always include at least one procedure in the reference boilerplate's `appRouter`. The `server/api/routers/example.ts` file with a `hello` query is the standard way.

### Prisma v7 — generated files must be gitignored

Add `/generated/` to the reference `.gitignore` before the first commit. Prisma 7 generates its client into `generated/` and these files must not be tracked.

### Tailwind v4 — `@import` not `@plugin` for tw-animate-css

`tw-animate-css` is a CSS file, not a JS Tailwind plugin. Use `@import "tw-animate-css"` in `globals.css`, not `@plugin`.

### monorepo `packages/ui` — `moduleResolution: "bundler"` required

React UI library packages consumed by bundlers (Next.js/Vite) need `moduleResolution: "bundler"` in their `tsconfig.json`, not `NodeNext`. `NodeNext` forces explicit `.js` extensions on all relative imports, which breaks the library.

### Next.js `headers()` not supported with `output: "export"`

Static export golden paths (`nextjs-static`, `monorepo/apps/marketing`) cannot use `async headers()` in `next.config.ts` — Next.js throws a build error. Security headers for static exports must be set at the hosting/CDN layer (Vercel `vercel.json`, Cloudflare `_headers`, Nginx `add_header`). Add comments to `next.config.ts` documenting this.

Server golden paths (`nextjs-fullstack`, `t3-stack`, `monorepo/apps/web`, `full-stack-rn/apps/web`, `full-stack-flutter/apps/web`) use `output: "standalone"` and fully support `async headers()`.

### `__YEAR__` and `__AUTHOR__` placeholders in LICENSE

`remap.py`'s `_customize_reference_files()` resolves `__YEAR__` using `datetime.datetime.now().year` at generation time. `__AUTHOR__` is intentionally left unresolved — it is a manual fill-in for the developer. Do not add `__AUTHOR__` to the placeholder map unless you have a reliable source for the author name in the pipeline.

---

## Language Extensions

The pipeline is written in Python and is mostly language-agnostic, but several parts contain TypeScript/React-specific assumptions. This section documents each one and how to extend it for a new language.

---

### `tools/figma/remap.py` — five extension points

#### 1. `DISCARD_STEMS` (line 16)

A set of file stems that are framework artifacts from Figma Make exports and must be discarded (not passed to the LLM). Currently contains only JS/TS config and infra stems.

**To extend**: add your framework's config/infra file stems.

```python
DISCARD_STEMS = {
    # existing JS/TS entries …

    # Django
    "settings", "wsgi", "asgi", "urls", "apps",
    # Rails
    "application", "routes", "environment",
    # Go
    "main", "go.mod",
}
```

Or, if you want per-golden-path discard lists instead of a global set, add a `"discardStems"` array to `manifest.json` and read it in `_classify()`:

```python
# In manifest.json
"discardStems": ["settings", "wsgi", "asgi"]

# In _classify() — remap.py
gp_discard = set(rules.get("discardStems", []))
if lower in DISCARD_STEMS or lower in gp_discard:
    return "discard"
```

#### 2. `INFRA_IMPORT_SIGNALS` (line 40)

Import strings that mark a Figma-exported file as infrastructure (not a UI component). Used to skip files that shouldn't be LLM-transformed.

**To extend**: add your framework's infra import paths.

```python
INFRA_IMPORT_SIGNALS = {
    # existing JS/TS entries …

    # Django
    "django.db", "django.contrib", "django.urls",
    # SQLAlchemy
    "sqlalchemy",
    # Rails (if Figma ever exports Ruby)
    "ActiveRecord", "ApplicationController",
}
```

Or move to a manifest-driven list: `"infraImportSignals": ["django.db", "sqlalchemy"]`.

#### 3. `SHADCN_PASSTHROUGH_SIGNALS` + `_is_shadcn_primitive()` (line 65)

The shadcn/ui auto-passthrough logic — files that import Radix UI or other shadcn primitives skip LLM transformation and are cleaned up and passed through directly.

This is entirely React-specific. For non-React paths, either:
- **Do nothing** — if no Figma files will match the signals, the check is harmless
- **Add a `"passthroughSignals"` array** to `manifest.json` and make `_is_shadcn_primitive()` read from the manifest:

```python
def _is_shadcn_primitive(content: str, gp_passthrough: list[str] | None = None) -> bool:
    signals = gp_passthrough if gp_passthrough is not None else list(SHADCN_PASSTHROUGH_SIGNALS)
    return any(sig in content for sig in signals)
```

```jsonc
// In manifest.json — Vue example using Radix Vue
"passthroughSignals": ["radix-vue", "@ark-ui/vue"]

// In manifest.json — Angular using PrimeNG
"passthroughSignals": ["primeng/"]

// In manifest.json — no passthrough needed
"passthroughSignals": []
```

#### 4. `_resolve_output_path()` path tokens (line 231)

Currently supports `{ComponentName}` (PascalCase stem) and `{domain}` (lowercase stem). The template comes from `manifest.json`'s `classification.categories.{cat}.outputPath`.

**To add custom tokens** for your framework (e.g. `{component_name}` snake_case, `{app_name}`, `{module}`):

```python
def _resolve_output_path(stem: str, category: str, rules: dict) -> str:
    categories = rules.get("categories", {})
    template = categories.get(category, {}).get("outputPath", "components/ui/{ComponentName}.tsx")
    path = template.replace("{ComponentName}", stem)
    if "{domain}" in path:
        path = path.replace("{domain}", stem.lower())
    # ── New tokens ──────────────────────────────
    if "{component_name}" in path:
        # snake_case: HeroSection → hero_section
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', stem).lower()
        path = path.replace("{component_name}", snake)
    if "{app_name}" in path:
        path = path.replace("{app_name}", "core")  # or derive from project_name
    # ────────────────────────────────────────────
    return path
```

#### 5. Queue file template (line 295)

Each queue file tells the agent what to do. The current template is TypeScript-centric ("Convert the Figma Make source below into enterprise-grade {golden_path} code", source block tagged ` ```tsx `).

For a non-TypeScript golden path, add a `"sourceLanguage"` field to `manifest.json` and use it to select the right code fence tag in the queue file:

```python
# In remap.py:_write_queue()
source_lang = gp_manifest.get("sourceLanguage", "tsx")

content = f"""\
...
### Figma Make source

```{source_lang}
{f['figma_source']}
```
"""
```

```jsonc
// In manifest.json
"sourceLanguage": "jsx"    // for React without TypeScript
"sourceLanguage": "vue"    // for Vue SFCs
"sourceLanguage": "html"   // for Django templates
"sourceLanguage": "tsx"    // default — TypeScript/React
```

---

### `tools/figma/validate.py` — adding golden-path-specific checks

`_run_checks()` is the single function where all validation lives. It receives `golden_path: str` so you can gate any check on path name.

**Pattern for a new language-specific check:**

```python
# ── Check N: [Your check name] ──────────────────────────────────
if golden_path == "your-path-name":
    if _YOUR_PATTERN_RE.search(content):
        errors.append(f"YOUR_ERROR_CODE: '{path}' [explanation and fix instruction]")
```

**Pattern for a check that applies to all paths EXCEPT yours:**

```python
# Example: "use client" check is irrelevant for Vite SPA and Vue SPA
if golden_path not in ("vite-spa", "vue-spa"):
    if _needs_use_client(content) and not _is_client_component(content):
        errors.append(...)
```

**Pattern for moving a check to manifest-driven config** (instead of hardcoding path names):

```jsonc
// In manifest.json
"validation": {
  "requireUseClient": true,
  "forbidProcessEnv": false,
  "forbidVitePatterns": false,
  "importAlias": "@/",
  "entryPoints": ["app/**/page.tsx", "app/**/layout.tsx"]
}
```

```python
# In _run_checks() — reads from manifest instead of golden_path string
validation_cfg = manifest.get("validation", {})

if validation_cfg.get("requireUseClient", False):
    if _needs_use_client(content) and not _is_client_component(content):
        errors.append(...)

if validation_cfg.get("forbidProcessEnv", False):
    if _PROCESS_ENV_RE.search(content):
        errors.append(...)
```

This is the preferred direction for future work — it eliminates the need to touch Python code when adding a new golden path.

---

### `_build_reachability()` — entry points for new frameworks

The import graph walker starts from framework-specific entry points:

```python
# Current hardcoded entry points in validate.py:_build_reachability()
# Next.js App Router → app/**/page.tsx, app/**/layout.tsx
# Vite SPA          → main.tsx, App.tsx, index.html
# CSS               → always reachable
```

For a new framework, add its entry points here, or move entry point patterns to `manifest.json`:

```jsonc
// In manifest.json
"validation": {
  "entryPoints": [
    "src/main.tsx",          // Vite
    "index.html",
    "src/**/*.vue"           // Vue — all SFCs are entries in a file-based router
  ]
}
```

```python
# In _build_reachability() — read from manifest
entry_patterns = manifest.get("validation", {}).get("entryPoints", [])
for pattern in entry_patterns:
    for path in all_paths:
        if pathlib.PurePath(path).match(pattern):
            roots.add(path)
```

---

## Complete Checklist

```
Boilerplate
[ ] golden_paths/{name}/reference/ created
[ ] reference/.gitignore — node_modules, generated/, build dirs, language-specific artifacts
[ ] reference/package.json (or pyproject.toml, Gemfile, go.mod) — ^ ranges or equiv
[ ] Zero typecheck / lint errors: pnpm typecheck (or mypy, srb tc, etc.)
[ ] reference/.nvmrc — Node version pin matching your runtime (e.g. "22")
[ ] reference/LICENSE — MIT (or project license) with __YEAR__ and __AUTHOR__ placeholders
[ ] reference/CHANGELOG.md — Keep a Changelog stub
[ ] reference/CONTRIBUTING.md — branch naming, workflow, commit format, code quality
[ ] reference/.github/dependabot.yml — automated dependency updates
[ ] reference/.github/PULL_REQUEST_TEMPLATE.md
[ ] reference/.github/ISSUE_TEMPLATE/bug_report.md
[ ] reference/.github/ISSUE_TEMPLATE/feature_request.md
[ ] reference/.github/workflows/ci.yml — all steps commented out; secrets documented in comments
[ ] Security headers: if output is "standalone" → add async headers() to next.config.ts; if output is "export" → add CDN-layer instructions as comments instead

Pipeline metadata
[ ] golden_paths/{name}/manifest.json
      ├── routing.srcDir is correct ("" or "src/")
      ├── tailwind.cssFile matches reference file path (or null for non-Tailwind stacks)
      ├── requiredFiles lists only always-present files
      ├── classification.categories covers all Figma component types
      └── sourceLanguage set if not tsx (optional — remap.py must read it)

Agent
[ ] .claude/agents/{name}.md
      ├── frontmatter: name + description with "golden_path is {name}"
      ├── Stack table versions match reference package.json
      └── Workflow section ends with: read queue → extract → write → self-review
                                      → update file tree → delete queue file → repeat

Python extension points (new language only)
[ ] remap.py: DISCARD_STEMS updated or manifest-driven discardStems added
[ ] remap.py: INFRA_IMPORT_SIGNALS updated or manifest-driven infraImportSignals added
[ ] remap.py: _is_shadcn_primitive() handles non-React passthrough or manifest-driven
[ ] remap.py: _resolve_output_path() handles any new {tokens} in outputPath templates
[ ] remap.py: queue file source_lang tag correct (tsx / vue / html / py / etc.)
[ ] validate.py: _run_checks() has any golden-path-specific checks
[ ] validate.py: _build_reachability() recognises new framework entry points

Documentation
[ ] MAINTENANCE.md — two sources of truth, quarterly sweep, known breaking patterns
[ ] GOLDEN_PATH_GUIDE.md — quick-select table, full profile, deployment table
```

---

## Naming Conventions

| What | Convention | Examples |
|------|-----------|---------|
| Golden path directory name | `kebab-case` | `nextjs-fullstack`, `vue-spa`, `django-htmx` |
| `manifest.json` name field | same as directory | `"name": "django-htmx"` |
| Agent `.md` file | `{name}.md` | `.claude/agents/django-htmx.md` |
| Agent frontmatter `name:` | same as directory | `name: django-htmx` |
| `package.json` `name` field | same or scoped | `"name": "django-htmx"` |

The name must be consistent across all four places — mismatches cause the pipeline to silently fall through to defaults.
