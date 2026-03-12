#!/usr/bin/env bash
# test-pipeline.sh — run the full Nexus pipeline locally, no n8n needed
# Usage: ./scripts/test-pipeline.sh [project_name] [golden_path] [zip_path_or_description]
#
# Examples:
#   ./scripts/test-pipeline.sh my-portfolio nextjs-static /tmp/figma-export.zip
#   ./scripts/test-pipeline.sh my-app nextjs-fullstack "A SaaS dashboard with login and analytics"
#   ./scripts/test-pipeline.sh my-app nextjs-fullstack --codebase /path/to/existing/project

set -euo pipefail

# ── args ────────────────────────────────────────────────────────────────────
PROJECT_NAME="${1:-my-app}"
GOLDEN_PATH="${2:-nextjs-fullstack}"
INPUT="${3:-}"

MCP_URL="http://localhost:3900/mcp"
CLAUDE_BIN="$HOME/.local/bin/claude"
CACHE_DIR="/tmp/nexus-${PROJECT_NAME}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
step() { echo -e "\n${CYAN}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }

# ── helpers ──────────────────────────────────────────────────────────────────
mcp_call() {
  local tool="$1"
  local input="$2"
  local result
  result=$(curl -s -X POST "$MCP_URL" \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"${tool}\",\"arguments\":${input}}}" \
    --max-time 120) || fail "MCP call failed (curl error) for tool: $tool"

  # Extract text from MCP response
  echo "$result" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if 'error' in r:
    print('MCP_ERROR: ' + json.dumps(r['error']), file=sys.stderr)
    sys.exit(1)
content = r.get('result', {}).get('content', [])
if content:
    text = content[0].get('text', '')
    print(text)
else:
    print('{}')
"
}

# ── check prerequisites ───────────────────────────────────────────────────────
step "Checking prerequisites"

curl -s --max-time 5 "$MCP_URL" > /dev/null 2>&1 || fail "MCP server not reachable at $MCP_URL — run: systemctl --user restart nexus-sse"
ok "MCP server reachable"

command -v "$CLAUDE_BIN" > /dev/null 2>&1 || fail "claude CLI not found at $CLAUDE_BIN"
ok "Claude CLI found"

# ── step 1: ingest ────────────────────────────────────────────────────────────
step "Step 1: Ingest"

if [[ "$INPUT" == "--codebase" ]]; then
  CODEBASE_PATH="${4:-}"
  [[ -z "$CODEBASE_PATH" ]] && fail "--codebase requires a path argument"
  ok "Mode: codebase → $CODEBASE_PATH"
  INGEST_RESULT=$(mcp_call "ingest_from_codebase" \
    "{\"project_dir\":\"${CODEBASE_PATH}\",\"golden_path\":\"${GOLDEN_PATH}\",\"project_name\":\"${PROJECT_NAME}\"}")
elif [[ -f "$INPUT" ]]; then
  ok "Mode: ZIP file → $INPUT"
  ZIP_B64=$(base64 -w0 "$INPUT" 2>/dev/null || base64 "$INPUT")
  INGEST_RESULT=$(mcp_call "ingest_figma_zip" \
    "{\"zip_base64\":\"${ZIP_B64}\",\"golden_path\":\"${GOLDEN_PATH}\",\"project_name\":\"${PROJECT_NAME}\"}")
elif [[ -d "$INPUT" ]]; then
  ok "Mode: directory → $INPUT"
  INGEST_RESULT=$(mcp_call "ingest_figma_zip" \
    "{\"project_dir\":\"${INPUT}\",\"golden_path\":\"${GOLDEN_PATH}\",\"project_name\":\"${PROJECT_NAME}\"}")
elif [[ -n "$INPUT" ]]; then
  ok "Mode: prompt → $INPUT"
  INGEST_RESULT=$(mcp_call "ingest_from_prompt" \
    "{\"description\":\"${INPUT}\",\"golden_path\":\"${GOLDEN_PATH}\",\"project_name\":\"${PROJECT_NAME}\"}")
else
  fail "No input provided. Pass a ZIP path, directory path, or description string."
fi

echo "$INGEST_RESULT" | python3 -c "
import sys, json
r = json.loads(sys.stdin.read())
if r.get('error'):
    print('INGEST ERROR: ' + str(r['error']))
    sys.exit(1)
print('  project_name :', r.get('project_name'))
print('  golden_path  :', r.get('golden_path'))
print('  source_type  :', r.get('source_type'))
comps = r.get('components', [])
print('  components   :', len(comps), '→', [c.get('name') for c in comps[:5]], '...' if len(comps) > 5 else '')
" || fail "Ingest failed — see output above"
ok "Ingest complete"

# ── step 2: remap ─────────────────────────────────────────────────────────────
step "Step 2: Remap to golden path"

REMAP_RESULT=$(mcp_call "remap_to_golden_path" \
  "{\"manifest_json\":$(echo "$INGEST_RESULT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))')}")

NEXUS_CACHE=$(echo "$REMAP_RESULT" | python3 -c "
import sys, json
r = json.loads(sys.stdin.read())
if r.get('error'):
    print('REMAP_ERROR: ' + str(r['error']), file=sys.stderr)
    sys.exit(1)
print(r.get('_nexus_cache', ''))
") || fail "Remap failed"

[[ -z "$NEXUS_CACHE" ]] && fail "remap_to_golden_path returned no _nexus_cache"
ok "Nexus cache: $NEXUS_CACHE"

# Check queue
QUEUE_COUNT=$(ls "$NEXUS_CACHE/05_queue/"*.md 2>/dev/null | wc -l | tr -d ' ')
if [[ "$QUEUE_COUNT" -eq 0 ]]; then
  warn "Queue is EMPTY — no components to transform. Checking why..."
  echo "  Files in cache:"
  ls "$NEXUS_CACHE/" 2>/dev/null || echo "  (cache dir missing)"
  echo "  File tree entries:"
  python3 -c "
import json, pathlib
ft = pathlib.Path('$NEXUS_CACHE/04_file_tree.json')
if ft.exists():
    d = json.loads(ft.read_text())
    files = d.get('files', [])
    print('  ', len(files), 'files in tree')
    for f in files[:10]:
        print('   -', f.get('path'))
    if len(files) > 10:
        print('   ... and', len(files)-10, 'more')
else:
    print('  04_file_tree.json NOT FOUND')
" 2>/dev/null
  warn "Pipeline will continue but no custom components will be transformed"
else
  ok "$QUEUE_COUNT queue files to transform:"
  ls "$NEXUS_CACHE/05_queue/"*.md | while read f; do echo "  - $(basename $f)"; done
fi

# ── step 3: transform (claude CLI) ───────────────────────────────────────────
if [[ "$QUEUE_COUNT" -gt 0 ]]; then
  step "Step 3: Transform queue (Claude CLI) — this may take several minutes"

  printf '%s\n' "Process all queue files in ${NEXUS_CACHE}/05_queue/. Each .md file is self-contained: read it and follow ALL instructions inside it exactly (transform the source code to match the golden path, update 04_file_tree.json, delete the queue file). After each file, list remaining .md files and continue until the directory is empty." \
    | timeout 1200 "$CLAUDE_BIN" --print --dangerously-skip-permissions \
        --model claude-sonnet-4-6 --allowedTools 'Read,Write,Edit,Bash'

  REMAINING=$(ls "$NEXUS_CACHE/05_queue/"*.md 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$REMAINING" -gt 0 ]]; then
    warn "$REMAINING queue files still unprocessed:"
    ls "$NEXUS_CACHE/05_queue/"*.md | while read f; do echo "  - $(basename $f)"; done
  else
    ok "All queue files processed"
  fi
else
  step "Step 3: Skipping transform (empty queue)"
fi

# ── step 4: validate ──────────────────────────────────────────────────────────
step "Step 4: Validate output"

VALIDATE_RESULT=$(mcp_call "validate_output" \
  "{\"file_tree_json\":$(echo "$REMAP_RESULT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))')}")

PASSED=$(echo "$VALIDATE_RESULT" | python3 -c "import sys,json; r=json.loads(sys.stdin.read()); print(r.get('passed', False))")
ERROR_COUNT=$(echo "$VALIDATE_RESULT" | python3 -c "import sys,json; r=json.loads(sys.stdin.read()); print(r.get('error_count', 0))")
WARNING_COUNT=$(echo "$VALIDATE_RESULT" | python3 -c "import sys,json; r=json.loads(sys.stdin.read()); print(r.get('warning_count', 0))")

echo "$VALIDATE_RESULT" | python3 -c "
import sys, json
r = json.loads(sys.stdin.read())
errors = r.get('errors', [])
warnings = r.get('warnings', [])
if errors:
    print('  ERRORS:')
    for e in errors: print('   ', e)
if warnings:
    print('  WARNINGS:')
    for w in warnings[:5]: print('   ', w)
    if len(warnings) > 5: print('   ...and', len(warnings)-5, 'more')
"

if [[ "$PASSED" == "True" ]]; then
  ok "Validation passed (0 errors, $WARNING_COUNT warnings)"
else
  warn "Validation: $ERROR_COUNT errors, $WARNING_COUNT warnings"

  # ── fix loop (max 3) ───────────────────────────────────────────────────────
  RETRY=0
  while [[ "$PASSED" != "True" && "$RETRY" -lt 3 ]]; do
    RETRY=$((RETRY + 1))
    step "Fix attempt $RETRY/3"

    printf '%s\n' "Read ${NEXUS_CACHE}/04_file_tree.json and fix ALL validation errors: (1) PASCALCASE_UI_FILE - any path like components/ui/Name.tsx where Name is uppercase: rename to lowercase in the path field (e.g. Button.tsx -> button.tsx). (2) MISSING_REQUIRED - any file path expected by the golden path that is absent from the files array: generate appropriate ${GOLDEN_PATH} content and add it. (3) BROKEN_IMPORT - any @/ import where the target file does not exist in the tree: fix the path to match an existing entry. After fixing all issues, write the corrected 04_file_tree.json back to disk." \
      | timeout 600 "$CLAUDE_BIN" --print --dangerously-skip-permissions \
          --model claude-sonnet-4-6 --allowedTools 'Read,Write,Edit,Bash'

    VALIDATE_RESULT=$(mcp_call "validate_output" \
      "{\"file_tree_json\":$(echo "$REMAP_RESULT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))')}")
    PASSED=$(echo "$VALIDATE_RESULT" | python3 -c "import sys,json; r=json.loads(sys.stdin.read()); print(r.get('passed', False))")
    ERROR_COUNT=$(echo "$VALIDATE_RESULT" | python3 -c "import sys,json; r=json.loads(sys.stdin.read()); print(r.get('error_count', 0))")

    if [[ "$PASSED" == "True" ]]; then
      ok "Validation passed after fix attempt $RETRY"
    else
      warn "Still $ERROR_COUNT errors after fix attempt $RETRY"
    fi
  done

  [[ "$PASSED" != "True" ]] && warn "Could not fully fix all errors — proceeding anyway with $ERROR_COUNT remaining"
fi

# ── step 5: package ───────────────────────────────────────────────────────────
step "Step 5: Package output"

PACKAGE_RESULT=$(mcp_call "package_output" \
  "{\"file_tree_json\":$(echo "$REMAP_RESULT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))')}")

ZIP_PATH=$(echo "$PACKAGE_RESULT" | python3 -c "
import sys, json
r = json.loads(sys.stdin.read())
if r.get('error'):
    print('PACKAGE_ERROR: ' + str(r['error']), file=sys.stderr)
    sys.exit(1)
print(r.get('zip_path', ''))
print('  total_files:', r.get('total_files'), file=sys.stderr)
print('  size_bytes :', r.get('size_bytes'), file=sys.stderr)
print('  has_files  :', bool(r.get('files')), file=sys.stderr)
") || fail "Package failed"

ok "ZIP at: $ZIP_PATH"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Pipeline complete!${NC}"
echo -e "  Project : $PROJECT_NAME"
echo -e "  ZIP     : $ZIP_PATH"
echo -e "  Run     : unzip $ZIP_PATH -d /tmp/out && cd /tmp/out/$PROJECT_NAME && pnpm install && pnpm dev"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
