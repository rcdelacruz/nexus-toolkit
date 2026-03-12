# TODO

## ~~Fix n8n workflow: prompt input type missing decomposition step~~ ✓ DONE

Decompose Description (Claude CLI) + Parse Decomposition nodes added to prompt route.
remap.py: sole-page → app/page.tsx promotion, default category fallback.
manifest.json (nextjs-static): default category + lowercase layout outputPath.
Prepare Fix Prompt: base64-encoded payload (fixes zsh parse error).
Verified working for nextjs-static golden path.

---

## Move all per-golden-path rules from Python into manifest.json

**Goal: adding or changing a golden path should only require editing `manifest.json` and the reference boilerplate — zero Python changes.**

Currently rules are hardcoded in `tools/figma/remap.py` and `tools/figma/validate.py`. The sections below list everything that needs to move.

---

### 1. Naming conventions

Add a `naming` block to each manifest:

```json
"naming": {
  "componentCase": "PascalCase",
  "uiFileCase": "lowercase",
  "rootEntryStems": ["app", "home", "homepage", "index", "landing", "root"]
}
```

| Field | Description |
|-------|-------------|
| `componentCase` | Casing for generated component filenames: `"PascalCase"`, `"camelCase"`, `"kebab-case"` |
| `uiFileCase` | Expected casing for `components/ui/` primitives: `"lowercase"` (shadcn) or `"PascalCase"`. Omit if not applicable. |
| `rootEntryStems` | Stem names that map to the root page (currently hardcoded as `ROOT_ENTRY_STEMS` in remap.py) |

**Python changes:** `remap.py` reads `naming.rootEntryStems` from manifest; `validate.py` reads `naming.uiFileCase` for the `PASCALCASE_UI_FILE` check.

---

### 2. Classification rules

Move out of hardcoded Python constants into manifest:

```json
"classification": {
  "discardStems": ["app", "index", "root", "main", "base", "next", ...],
  "sectionKeywords": ["hero", "banner", "cta", "pricing", "testimonial", ...],
  "componentSuffixes": ["screen", "view", "widget", "page", "route", "form", ...]
}
```

| Field | Description |
|-------|-------------|
| `discardStems` | Stems that are framework artifacts and should be discarded (currently `DISCARD_STEMS` in remap.py) |
| `sectionKeywords` | Keywords that classify a component as a section (currently `SECTION_KEYWORDS` in remap.py) |
| `componentSuffixes` | Suffixes stripped when deriving route slugs (currently `_COMPONENT_SUFFIXES` in remap.py) |

**Python changes:** `remap.py` reads all three from manifest instead of module-level constants.

---

### 3. Validation rules

Each golden path should declare which checks apply to it:

```json
"validation": {
  "checks": {
    "useClient": true,
    "noProcessEnv": false,
    "noOklch": true,
    "noTailwindConfig": true,
    "noConsoleLog": true,
    "noHardcodedHex": true,
    "noInlineStyles": true,
    "namedExportsOnly": true,
    "noBareLreactImport": true
  }
}
```

Currently `validate.py` hardcodes which checks run and uses `if golden_path == "vite-spa"` guards scattered through the code. Each check should be toggled by the manifest instead.

**Python changes:** `validate.py` loads the manifest for the golden path being validated and gates each check on the manifest flag.

---

### 4. Tailwind rules (partial — extend existing `tailwind` block)

Already has `version`, `cssFile`, `configFile`. Add:

```json
"tailwind": {
  "allowConfig": false,
  "allowOklch": false,
  "tokenDirective": "@theme inline"
}
```

Currently `noTailwindConfig` and `noOklch` are unconditional in `validate.py`.

---

### Files to update

**Python:**
- [ ] `tools/figma/remap.py`
- [ ] `tools/figma/validate.py`

**Manifests:**
- [ ] `nextjs-fullstack/manifest.json`
- [ ] `nextjs-static/manifest.json`
- [ ] `t3-stack/manifest.json`
- [ ] `vite-spa/manifest.json`
- [ ] `monorepo/manifest.json`
- [ ] `full-stack-rn/manifest.json`
- [ ] `full-stack-flutter/manifest.json`

---

## Multi-LLM CLI support

**Goal: support LLM CLIs other than `claude` in `nexus transform` / `nexus run`.**

Add a `--llm` flag with an adapter pattern per LLM:

```bash
nexus run prompt "My app" -g nextjs-fullstack --llm claude   # default
nexus run prompt "My app" -g nextjs-fullstack --llm gemini
```

### Tasks
- [ ] Add `--llm` flag to `nexus transform` and all `nexus run` commands (default: `claude`)
- [ ] Abstract LLM invocation into `_run_llm(llm, claude_path, model, ...)` in `nexus_cli.py`
- [ ] Add adapter for `gemini` CLI (different flags, system prompt syntax)
- [ ] Add adapter for `openai` CLI
- [ ] Document supported LLMs in `docs/PUBLISHING.md` and `nexus.coderstudio.co/docs`

---

## ~~DevSecOps CLI + MCP (Phase 1 — Agent-based)~~ ✓ DONE

**Implemented:** 22 dev-workflow agents + `run_agent` / `list_agents` MCP tools + `nexus agent` / `nexus workflow` CLI + 7 n8n DevSecOps workflows (ds1–ds7).

**Agent categories:** `cross-cutting` (11), `architecture` (3), `javascript` (4), `savants` (4)

**n8n workflows:** `ds1-code-review.json`, `ds2-security-scan.json`, `ds3-db-review.json`, `ds4-qa-gate.json`, `ds5-deploy-review.json`, `ds6-weekly-audit.json`, `ds7-health-check.json`

**Architecture decision:** n8n as entry point (Auth Guard) → Nexus MCP `run_agent` → `claude` CLI via SSH. No custom auth in CLI.

**Reference:** https://cdn.stratpoint.io/Stratpoint_DevSecOps_Flow.html

---

### Remaining / Phase 2

For deeper per-DS-step analysis (Gitleaks secrets scanning, GitHub issue creation, IaC Terraform parsing, etc.), implement dedicated `nexus ds` subcommands:

```bash
nexus ds code-review <diff>         # DS-1 (deeper than run_agent)
nexus ds security-scan <dir>        # DS-2 (+ Gitleaks)
nexus ds db-review <migrations>     # DS-3
nexus ds qa-gate <dir>              # DS-4 (+ GitHub issue creation)
nexus ds deploy-review <iac-dir>    # DS-5 (Terraform/Docker/K8s)
nexus ds health-check <url>         # DS-7
nexus ds weekly-audit               # DS-6
```

### Phase 2 Tasks
- [ ] Design unified output schema (structured findings → Google Chat / PostgreSQL)
- [ ] Implement `nexus ds` subcommand group in `nexus_cli.py`
- [ ] DS-2: Integrate Gitleaks for secrets detection
- [ ] DS-4: GitHub issue creation for coverage gaps
- [ ] DS-5: Parse Terraform/Docker/K8s IaC files
- [ ] DS-6: SSH repo clone + consolidated multi-repo report
- [ ] Google Chat webhook integration (direct, not via n8n)
- [ ] PostgreSQL logging integration (direct)
