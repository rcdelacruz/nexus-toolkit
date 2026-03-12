# Agents Architecture Guide

This guide covers the three agent systems in Nexus MCP — how they are structured, how data flows through them, and how they relate to each other.

---

## Three Agent Namespaces

| Namespace | Source | Count | Triggered by | Purpose |
|-----------|--------|-------|--------------|---------|
| **Golden Path** | `tools/agents/` | 8 | `remap_to_golden_path` (MCP) | Figma → production code transformation |
| **Dev-Workflow** | `tools/dev-agents/` | 22 | `run_agent` (MCP) · `nexus agent run` (CLI) | Software Development Lifecycle (SDLC) assistance: review, security, QA, deploy |
| **Workflow Commands** | `.claude/commands/` | 11 | `/workflow-*` (Claude Code) · `nexus workflow run` (CLI) | Multi-step orchestration (design → implement → deploy) |

All three are registered as symlinks in `.claude/agents/` and `.claude/commands/` so Claude Code can invoke them directly. Golden path and dev-workflow agents share the directory but have no name collisions — golden paths use stack names (`nextjs-fullstack`, `t3-stack`) while dev-workflow agents use role names (`code-reviewer`, `security`).

---

## Static Architecture

```mermaid
graph TB
    subgraph SERVER["nexus_server.py — FastMCP"]
        direction TB
        ST["register_search_tools\nnexus_search · nexus_read"]
        FT["register_figma_tools\ningest_figma_zip · ingest_from_prompt\ningest_from_codebase · remap_to_golden_path\nvalidate_output · package_output\nupdate_file_in_tree"]
        DT["register_devsecops_tools\nrun_agent · list_agents"]
    end

    subgraph CLI["nexus_cli.py — Typer"]
        direction TB
        PI["nexus ingest / remap / transform\nvalidate / package / run"]
        AG["nexus agent list\nnexus agent run"]
        WF["nexus workflow run"]
    end

    subgraph AGENTS["Agent Source Files"]
        direction TB
        GP["tools/agents/\nnextjs-fullstack.md · nextjs-static.md\nt3-stack.md · vite-spa.md · monorepo.md\nfull-stack-rn.md · full-stack-flutter.md\nnexus-validator.md"]
        DA["tools/dev-agents/\narchitecture/  ·  cross-cutting/\njavascript/  ·  savants/"]
        WC["\.claude/commands/\nworkflow-review-code.md\nworkflow-deploy.md · …(11 total)"]
    end

    subgraph SYMLINKS["\.claude/ — Claude Code entry points"]
        direction LR
        SA["agents/\n(30 symlinks)"]
        SC["commands/\n(11 symlinks)"]
    end

    subgraph N8N["n8n — Orchestration"]
        DS["DS-1…DS-7\nWebhook / Cron → Auth Guard\n→ SSH curl → MCP run_agent"]
    end

    CLAUDE["claude CLI\n(subprocess)"]

    FT -->|"embeds agent rules\nin queue files"| GP
    DT -->|"_load_dev_agent()"| DA
    AG -->|"--system-prompt"| DA
    WF -->|"workflow text\nas prompt"| WC
    PI -->|"nexus transform\nspawns subagent"| GP

    GP -->|"symlinks"| SA
    DA -->|"symlinks"| SA
    WC -->|"symlinks"| SC

    DT --> CLAUDE
    AG --> CLAUDE
    WF --> CLAUDE
    PI --> CLAUDE

    DS -->|"POST /mcp\nrun_agent tool"| DT
```

---

## Golden Path Agent — Data Flow

The golden path agent is invoked as a Claude Code subagent during the LLM transform step. The queue files are self-contained: each one embeds the full agent rules so no external file read is needed during transformation.

```mermaid
sequenceDiagram
    participant User
    participant MCP as Nexus MCP Server
    participant FS as /tmp/nexus-{project}/
    participant Agent as Golden Path Agent<br/>(Claude Code subagent)

    User->>MCP: ingest_figma_zip / ingest_from_prompt / ingest_from_codebase
    MCP->>FS: writes 01_manifest.json

    User->>MCP: remap_to_golden_path(manifest_json)
    MCP->>FS: seeds golden_paths/{gp}/reference/ boilerplate
    MCP->>FS: classifies components → writes 04_file_tree.json
    MCP->>FS: writes 05_queue/001_Button.md … (one .md per component)
    Note over FS: each queue file embeds:<br/>• output path + category<br/>• Project components: list<br/>• full agent rules (inline)
    MCP-->>User: returns _nexus_cache + spawn instructions

    User->>Agent: spawns golden path agent with _nexus_cache

    loop until 05_queue/ is empty
        Agent->>FS: lists 05_queue/ → sees remaining work
        Agent->>FS: reads 04_file_tree.json → full tree + reference_paths
        Agent->>FS: reads next queue file (e.g. 001_Button.md)
        Note over Agent: transforms source → production component<br/>uses Project components: guard<br/>(never imports reference stubs)
        Agent->>FS: writes transformed file
        Agent->>MCP: update_file_in_tree(path, content, nexus_cache)
        Agent->>FS: deletes queue file
    end

    User->>MCP: validate_output(file_tree_json)
    MCP->>FS: reads 04_file_tree.json → runs 26 checks
    MCP-->>User: { passed, error_count, errors[], warnings[] }

    alt validation failed (max 3 retries)
        User->>Agent: spawns nexus-validator agent with fix prompt
        Agent->>FS: fixes errors → updates 04_file_tree.json
        User->>MCP: validate_output (retry)
    end

    User->>MCP: package_output(file_tree_json)
    MCP->>FS: reachability analysis → strip orphans → ZIP
    MCP-->>User: { zip_path, total_files, size_bytes }
```

### Queue file anatomy

```
05_queue/001_HeroSection.md
─────────────────────────────────────────────────────────
# Transform: HeroSection

**Output path:** app/components/HeroSection.tsx
**Category:** section

**Project components:**
- app/components/HeroSection.tsx
- app/components/NavBar.tsx
- app/components/Footer.tsx

**Agent rules:**
[full contents of tools/agents/nextjs-fullstack.md embedded here]

---

**Source:**
[original Figma Make source code]
```

---

## Dev-Workflow Agent — Data Flow

Dev-workflow agents have two equivalent entry points: the `run_agent` MCP tool (used by n8n and Claude Code) and `nexus agent run` (used from the terminal). Both call the `claude` CLI with the agent markdown as a system prompt.

```mermaid
flowchart TD
    subgraph CALLERS["Callers"]
        CC["Claude Code\n(MCP client)"]
        N8N["n8n\n(HTTP POST to /mcp)"]
        CLI["Terminal\nnexus agent run"]
    end

    subgraph MCP_TOOL["run_agent MCP tool\n(agent_runner.py)"]
        LA["_load_dev_agent(name)\n① registry lookup\n② rglob fallback\n③ installed-path fallback"]
        LW["_load_workflow(name)\n.claude/commands/ → docs/ fallback"]
        FC["_find_claude()\nPATH → ~/.local/bin/claude"]
        BUILD["build cmd:\nclaude --print\n--dangerously-skip-permissions\n--model {model}\n--system-prompt {agent.md}\n{context}"]
        RUN["subprocess.run(cmd, timeout=300)"]
        OUT["return JSON:\n{ agent, workflow, findings, model }"]
    end

    subgraph CLI_PATH["nexus agent run\n(nexus_cli.py)"]
        FD["_find_dev_agent(name)\nsame registry + fallback"]
        INPUT["read context:\nfile · stdin · --context flag"]
        BUILD2["build cmd:\nclaude --print\n--system-prompt {agent.md}\n{context}"]
        RUN2["subprocess.run → stream stdout"]
    end

    CC -->|"run_agent(name, context)"| MCP_TOOL
    N8N -->|"POST /mcp\n{ tool: run_agent, ... }"| MCP_TOOL
    CLI --> CLI_PATH

    LA --> FC
    LW -.->|"optional workflow prefix"| BUILD
    FC --> BUILD
    BUILD --> RUN
    RUN --> OUT

    FD --> INPUT
    INPUT --> BUILD2
    BUILD2 --> RUN2
```

### Agent loading — fallback chain

```mermaid
flowchart LR
    A["_load_dev_agent(name)"] --> B{"registry\nlookup"}
    B -->|"found"| C["tools/dev-agents/{subdir}/{name}.md"]
    B -->|"not in registry"| D{"rglob across\ntools/dev-agents/"}
    D -->|"found"| E["first match"]
    D -->|"not found"| F{"rglob relative\nto __file__"}
    F -->|"found"| G["uvx-installed path\ne.g. ~/.local/share/uv/tools/..."]
    F -->|"not found"| H["FileNotFoundError\n'Available agents: ...'"]
```

The same three-step fallback runs in both `agent_runner.py` (MCP) and `nexus_cli.py` (CLI), ensuring the same agent is found whether running from a dev checkout or a `uvx`-installed distribution.

---

## Dev-Workflow Agent Categories

```mermaid
mindmap
  root((dev-agents))
    cross-cutting
      code-reviewer
      security
      database
      deployment
      monitoring
      performance
      product-manager
      qa-tester
      task-planner
      tech-writer
      test-planner
    architecture
      software-architect
      solution-architect
      solution-designer
    javascript
      backend-api
      frontend-ui
      fullstack-nextjs
      react-native
    savants
      savant-fullstack-js
      savant-flutter
      savant-java-spring
      savant-react-native
```

---

## n8n DevSecOps Pipeline — Data Flow

Seven n8n workflows wire the dev-workflow agents to real CI/CD events. Each workflow follows the same pattern: trigger → auth → extract context → MCP call → parse → notify.

```mermaid
flowchart TD
    subgraph TRIGGERS["Triggers"]
        GH["GitHub Webhook\n(PR opened / push)"]
        MERGE["GitHub Webhook\n(merge to develop)"]
        PROD["GitHub Webhook\n(promote to production)"]
        CRON["Cron\nMon 09:00"]
        DEPLOY["Post-deploy\nWebhook"]
    end

    subgraph AUTH["Auth Guard\n(shared sub-workflow)"]
        HMAC["HMAC signature\nverification"]
    end

    subgraph WORKFLOWS["n8n DevSecOps Workflows"]
        DS1["DS-1 · ds1-code-review.json\ncode-reviewer agent\n→ advisory PR comment"]
        DS2["DS-2 · ds2-security-scan.json\nsecurity agent\n→ can block merge"]
        DS3["DS-3 · ds3-db-review.json\ndatabase agent\n(migrations only)"]
        DS4["DS-4 · ds4-qa-gate.json\nqa-tester agent\n→ after merge to develop"]
        DS5["DS-5 · ds5-deploy-review.json\ndeployment agent\n→ before production"]
        DS6["DS-6 · ds6-weekly-audit.json\nsecurity agent\n→ cron, saves to Postgres"]
        DS7["DS-7 · ds7-health-check.json\nmonitoring agent\n→ post-deploy"]
    end

    subgraph MCP_CALL["MCP call (SSH node)"]
        B64["base64-encode JSON payload\n{ tool: run_agent, agent_name, context }"]
        SSH["SSH to server\necho b64 | base64 -d | curl -X POST\nhttp://localhost:3900/mcp"]
        PARSE["parse response\n{ findings: '...' }"]
    end

    subgraph NOTIFY["Output"]
        CHAT["Google Chat\nwebhook notification"]
        PG["PostgreSQL\naudit log (DS-6)"]
        BLOCK["Block merge\n(DS-2, DS-3 critical)"]
    end

    GH --> AUTH
    MERGE --> AUTH
    PROD --> AUTH
    CRON --> DS6
    DEPLOY --> AUTH

    AUTH --> DS1
    AUTH --> DS2
    AUTH --> DS3
    AUTH --> DS4
    AUTH --> DS5
    AUTH --> DS7

    DS1 --> MCP_CALL
    DS2 --> MCP_CALL
    DS3 --> MCP_CALL
    DS4 --> MCP_CALL
    DS5 --> MCP_CALL
    DS6 --> MCP_CALL
    DS7 --> MCP_CALL

    MCP_CALL --> NOTIFY

    DS2 -->|"critical findings"| BLOCK
    DS3 -->|"destructive migration"| BLOCK
    DS6 --> PG
```

### MCP call anatomy (n8n SSH node)

Each n8n workflow constructs the MCP call as a base64-encoded curl command to avoid shell escaping issues across SSH:

```
JavaScript node → builds JSON payload:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "run_agent",
    "arguments": {
      "agent_name": "code-reviewer",
      "context": "<PR diff extracted above>",
      "model": "claude-sonnet-4-6"
    }
  },
  "id": 1
}

SSH node executes:
  B64=$(echo '<json>' | base64 -w0)
  echo "${B64}" | base64 -d | curl -s -X POST http://localhost:3900/mcp \
    -H 'Content-Type: application/json' -d @-
```

The Nexus MCP server has `stateless_http=True` so no prior `initialize` handshake is needed — each call is self-contained.

---

## Workflow Commands — Data Flow

Workflow commands are multi-step orchestration instructions. Unlike agents (which are system prompts), workflow commands are user-level prompts — Claude reads the workflow steps and executes them against the provided context.

```mermaid
flowchart TD
    subgraph WORKFLOWS["Workflow Commands (.claude/commands/)"]
        WRC["workflow-review-code.md\nStep 1: check complexity\nStep 2: check patterns\nStep 3: check security\nStep 4: summarise findings"]
        WRS["workflow-review-security.md"]
        WD["workflow-deploy.md"]
        WIF["workflow-implement-fullstack.md"]
        WDA["workflow-design-architecture.md"]
    end

    subgraph CLAUDE_CODE["Claude Code (slash commands)"]
        SLASH["/workflow-review-code\n→ loads .claude/commands/ file\n→ runs workflow steps"]
    end

    subgraph CLI["nexus workflow run"]
        WR["nexus workflow run\nworkflow-review-code src/api.ts\n→ _find_workflow()\n→ prepend workflow + context\n→ subprocess claude --print"]
    end

    subgraph RUN_AGENT["run_agent MCP tool (workflow= param)"]
        RA["run_agent(\n  agent_name='code-reviewer',\n  context='...',\n  workflow='workflow-review-code'\n)\n→ prepends workflow to context\n→ agent is still system prompt"]
    end

    WORKFLOWS --> CLAUDE_CODE
    WORKFLOWS --> CLI
    WORKFLOWS --> RUN_AGENT
```

The `workflow=` parameter in `run_agent` combines both: the **dev-workflow agent** as a system prompt (role and expertise) and the **workflow command** as structured steps prepended to the user context.

---

## How Agent Rules Reach Claude

```mermaid
flowchart LR
    subgraph SOURCE["Source .md files"]
        A["tools/agents/nextjs-fullstack.md\n(golden path rules)"]
        B["tools/dev-agents/cross-cutting/\ncode-reviewer.md\n(dev-workflow rules)"]
        C[".claude/commands/\nworkflow-review-code.md\n(workflow steps)"]
    end

    subgraph PACKAGING["How they reach Claude"]
        D["remap embeds agent .md\ninto each 05_queue/*.md\n(self-contained, no runtime load)"]
        E["run_agent loads .md\npasses as --system-prompt flag"]
        F["nexus agent run loads .md\npasses as --system-prompt flag"]
        G["nexus workflow run loads .md\nprepends to --print prompt"]
        H["Claude Code loads .md\nvia .claude/agents/ symlink\n(native subagent)"]
    end

    A --> D
    A --> H
    B --> E
    B --> F
    B --> H
    C --> G
    C --> H
```

---

## Adding a New Dev-Workflow Agent

1. **Write the agent:** `tools/dev-agents/{category}/{name}.md`
2. **Register it:** add `"name": "category"` to `_AGENT_REGISTRY` in `tools/devsecops/agent_runner.py` and `_DEV_AGENT_REGISTRY` in `nexus_cli.py`
3. **Symlink for Claude Code:** `.claude/agents/{name}.md → ../../tools/dev-agents/{category}/{name}.md`
4. **Update `pyproject.toml`** package-data if adding a new category subdirectory
5. **Bump version** and deploy via PyPI (Python files changed)

No changes needed to `nexus_server.py` — `register_devsecops_tools` reads the registry at import time.

---

## Adding a New Workflow Command

1. **Write the workflow:** `.claude/commands/{name}.md` (also copy to `docs/sample-claude-agents/commands/` as reference)
2. **No registration needed** — `_find_workflow` scans `.claude/commands/` by filename
3. Available immediately in Claude Code as `/{name}` and via `nexus workflow run {name}`
