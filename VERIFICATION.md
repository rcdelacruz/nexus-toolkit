# How to Verify Nexus MCP Server is Working

## Installation

```bash
claude mcp add nexus -- uvx --from git+https://github.com/rcdelacruz/nexus-mcp.git@multi-source-ingestion nexus-mcp
```

## Server Connection

```bash
$ claude mcp list
nexus: ... - ✓ Connected
```

After connecting you should see **8 tools** available:

| Tool | Category |
|------|----------|
| `nexus_search` | Search |
| `nexus_read` | Search |
| `ingest_figma_zip` | Pipeline |
| `ingest_from_prompt` | Pipeline |
| `ingest_from_codebase` | Pipeline |
| `remap_to_golden_path` | Pipeline |
| `validate_output` | Pipeline |
| `package_output` | Pipeline |

---

## Testing Search Tools

### nexus_search

```
Search for "Python asyncio documentation" using docs mode
```

Expected output: formatted list of results with title, URL, snippet.

### nexus_read

```
Use nexus_read to read https://docs.python.org/3/library/asyncio.html
```

Expected output: clean extracted content, headers and code blocks only (auto-detects docs site).

---

## Testing Pipeline Tools

### Option A — Figma Make export

If you have a Figma Make export unzipped locally:

```
I have a Figma Make export at /path/to/figma-export.
Turn it into a Next.js fullstack app called "my-app".
```

### Option B — Text description (no Figma file)

```
Build a SaaS landing page with a hero, features grid, and pricing table.
Use nextjs-static. Call it "landing".
```

### Option C — Existing codebase migration

```
Migrate my existing React app at /path/to/old-app to nextjs-fullstack conventions.
Call the output "new-app".
```

All three options chain the same pipeline automatically:
1. Ingestion tool → manifest
2. `remap_to_golden_path` → seeds boilerplate + queues components
3. Golden path agent → transforms each component
4. `validate_output` → static analysis
5. `package_output` → ZIP download

---

## /mcp Command

In any Claude Code conversation:

```
/mcp
```

Expected:
```
Connected MCP Servers:
- nexus (8 tools)
  - nexus_search
  - nexus_read
  - ingest_figma_zip
  - ingest_from_prompt
  - ingest_from_codebase
  - remap_to_golden_path
  - validate_output
  - package_output
```

---

## Debugging

1. **Check server status:**
   ```bash
   claude mcp list
   ```

2. **Restart Claude Code** — MCP connections require a restart after config changes.

3. **Check logs:**
   ```bash
   cat ~/.local/state/claude/logs/mcp-*.log
   ```
