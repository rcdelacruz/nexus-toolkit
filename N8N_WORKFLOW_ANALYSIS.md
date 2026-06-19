# n8n Workflow Analysis

> Generated: March 13, 2026 · 33 workflows across 7 functional groups

---

## Inventory

| # | Workflow | Group | Active | Trigger |
|---|----------|-------|--------|---------|
| 1 | Auth: Login with Cookie | Auth | ✅ | POST /auth/login |
| 2 | Auth: Validate Session | Auth | ✅ | GET /auth/verify |
| 3 | Auth: Logout | Auth | ✅ | POST /auth/logout |
| 4 | Auth Guard (Sub-Workflow) | Auth | ✅ | Sub-workflow call |
| 5 | API Key: Create | API Keys | ✅ | POST /api-keys/create |
| 6 | API Key: List | API Keys | ✅ | GET /api-keys |
| 7 | API Key: Revoke | API Keys | ✅ | POST /api-keys/revoke |
| 8 | User Management: Invite User | Users | ✅ | POST /users/invite |
| 9 | User Management: Approve User | Users | ✅ | POST /users/approve |
| 10 | User Management: Delete User | Users | ✅ | POST /users/delete |
| 11 | User Management: Get All Users | Users | ✅ | GET /users |
| 12 | Step 0: Delete Project Workflow | SDLC | ✅ | - |
| 13 | Step 1: Project Setup | SDLC | ✅ | POST /setup-project |
| 14 | Step 2: PRD Generation | SDLC | ✅ | POST /create-prd |
| 15 | Step 3: Dev Tasks Generation | SDLC | ✅ | POST /create-tasks |
| 16 | Approve PRD | SDLC | ✅ | POST /approve-prd |
| 17 | Cancel Workflow | SDLC | ✅ | - |
| 18 | Close Project | SDLC | ✅ | - |
| 19 | Generate BRD | SDLC | ✅ | - |
| 20 | Get All Projects | Query | ✅ | GET /projects |
| 21 | Get Project Status | Query | ✅ | GET /project-status |
| 22 | Get Project Activity | Query | ✅ | GET /project-activity |
| 23 | Get Nexus Job Status | Query | ✅ | GET /status/:projectName |
| 24 | Nexus Design-to-Code | Pipeline | ✅ | POST (MCP/webhook) |
| 25 | Notify: Google Chat (Sub-Workflow) | Notification | ✅ | Sub-workflow call |
| 26 | Error Handler - Update Failed Status | Error | ✅ | Error trigger |
| 27 | DS-1: Code Review | DevSecOps | ❌ | POST /devsecops/code-review |
| 28 | DS-2: Security Scan | DevSecOps | ❌ | POST /devsecops/security-scan |
| 29 | DS-3: DB Migration Review | DevSecOps | ❌ | POST /devsecops/db-review |
| 30 | DS-4: QA Gate | DevSecOps | ❌ | POST /devsecops/qa-gate |
| 31 | DS-5: Deployment Review | DevSecOps | ❌ | POST /devsecops/deploy-review |
| 32 | DS-6: Weekly Security Audit | DevSecOps | ❌ | Cron (Mon 9am) |
| 33 | DS-7: Post-Deploy Health Check | DevSecOps | ❌ | POST /devsecops/health-check |

---

## System Architecture

### Top-Level View

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend / CI / GitHub Webhooks                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────────────┐
│  n8n Webhooks  (ai-project/v1/*)  &  (devsecops/*)             │
└──────┬──────────────────┬───────────────────────────────────────┘
       │                  │
       ▼                  ▼
 Auth Guard          SDLC Pipeline
 Sub-Workflow        Workflows
 (session/API key/   Step 1 → 2 → 3
  HMAC/GitLab/        ↓
  X-User-Email)    Nexus Design-to-Code
                      │ SSH / MCP Client
                      ▼
               Nexus MCP Server (:3900)
                      │
                      ▼
               claude CLI (SSH)
                      │
        ┌─────────────┴──────────────┐
        │                            │
      Google Drive               Postgres DB
      (BRD/PRD/Tasks)            (projects, sessions,
                                  users, api_keys,
                                  nexus_jobs, audits)
```

### Shared Infrastructure Nodes (used by many workflows)
- **Auth Guard** (`33ehIaQultvJQW4K`) — every authenticated endpoint calls this first
- **Notify: Google Chat** (`G2SEoq84kLWf054f`) — all notifications route through here
- **Error Handler** (`IYX78duIffflObuQ`) — registered as `errorWorkflow` in all DS workflows

---

## Group-by-Group Analysis

### 1. Authentication System

#### `Auth: Login with Cookie`
- Validates a Google JWT id_token against `https://oauth2.googleapis.com/tokeninfo`
- **Domain lock**: only tokens with `email.endsWith('@stratpoint.com')` are accepted
- On success: generates a session token (`crypto.randomBytes(32)`), inserts to `sessions` table, sets `HttpOnly; Secure; SameSite=Strict` cookie (7-day expiry)
- On failure: returns 401 with `error_description` from Google's response

#### `Auth: Validate Session`
- Reads `ai_project_session` cookie, runs parameterized SQL (`$1`) against `sessions JOIN users` — correctly uses prepared statement
- Checks `expires_at > NOW()` and `user.status = 'active'`
- Updates `last_activity` if last update was > 5 minutes ago
- Returns user profile (email, name, picture, role) on success

#### `Auth Guard (Sub-Workflow)`
Supports **5 auth mechanisms** in priority order:
1. `ai_project_session` cookie
2. `x-api-key` header
3. `x-hub-signature-256` (GitHub HMAC webhook)
4. `x-gitlab-token` (GitLab webhook)
5. `x-user-email` header (lightweight frontend auth)

After extraction, routes to the appropriate validator branch. Returns a normalized `{ authenticated, authMethod, userEmail, userRole }` object.

---

### 2. SDLC Project Pipeline

#### `Step 1: Project Setup`
- Creates project folder structure in **Google Drive** (`01-Input/`, `02-Output/`, `03-Work/`)
- Copies template documents from a shared templates folder
- Registers the project in Postgres `projects` table
- Source of `createdBy` identity: `headers['x-user-email']` (no full auth guard, relies on upstream call)

#### `Step 2: PRD Generation`
- Accepts a BRD PDF upload (max 10MB, PDF-only validation)
- Validates file type and size before processing
- Stores PDF in Google Drive `01-Input/` folder
- Calls `claude` CLI via SSH with product-manager agent
- Supports `regenerate` flag to overwrite an existing PRD
- Custom prompt options: `template`, `detailLevel`, `includeDiagrams`, `focusSecurity`, `prioritizePerformance`, `customInstructions`
- Workaround for n8n binary data loss: `Restore Binary After DB` node re-attaches binary after every Postgres query

#### `Step 3: Dev Tasks Generation`
- Fetches PRD from Google Drive, extracts to text
- Calls `claude` CLI via SSH to extract 3–10 epics as structured JSON
- Loops over each epic (via `splitInBatches`), generating detailed task lists per epic
- **Fallback**: if epic extraction fails to return valid JSON, hardcodes 3 generic epics and silently continues

#### `Approve PRD`
- Looks up project in DB, verifies PRD file exists
- Updates `prd_status = 'approved'` in Postgres
- Notifies Google Chat

---

### 3. Nexus Design-to-Code Pipeline

The most complex workflow. Orchestrates the full pipeline over SSH and MCP:

```
Webhook
   │
   ├─► Prepare Input (project_name, golden_path, zip_base64)
   │
   ├─► Ingest (MCP Client → ingest_figma_zip/ingest_from_prompt/ingest_from_codebase)
   │        └─► Check Ingest Output
   │
   ├─► Remap to Golden Path (MCP Client → remap_to_golden_path)
   │
   ├─► Transform (SSH → claude CLI with golden path agent)
   │        └─► reads 05_queue/, processes each file
   │
   ├─► Validate Output (MCP Client → validate_output)
   │        └─► Check Validate Result
   │              ├─► PASS → Package Output
   │              └─► FAIL → Prepare Fix Prompt
   │                           └─► Fix Validation Errors (SSH → claude CLI)
   │                                └─► Re-Validate → (max 3 retries)
   │
   ├─► Package Output (MCP Client → package_output)
   │
   ├─► Create GitHub Repo (GitHub API)
   │
   ├─► Push code to repo (SSH → git)
   │
   ├─► Cleanup /tmp (SSH → rm -rf)
   │
   └─► Respond to Webhook
```

Fix prompt is **base64-encoded** before passing to shell — correct approach that avoids shell injection from error messages.

---

### 4. DevSecOps Automation (DS-1 through DS-7)

All 7 follow the same 8-node pattern:

```
Webhook / Cron
   │
   ├─► Auth Guard (sub-workflow)
   │
   ├─► IF Authenticated?
   │     ├─► NO  → Respond 401
   │     └─► YES → Extract Context
   │                  │
   │                  ├─► Build MCP Request (base64-encode JSON-RPC payload)
   │                  │
   │                  ├─► SSH → curl → Nexus MCP run_agent
   │                  │
   │                  ├─► Parse Output
   │                  │
   │                  ├─► Notify Google Chat
   │                  │
   │                  └─► Respond 200
```

| Workflow | Agent | Trigger Event | Extra |
|----------|-------|---------------|-------|
| DS-1 | `code-reviewer` + `workflow-review-code` | PR opened/updated | Reviews diff |
| DS-2 | `security` + `workflow-review-security` | PR opened/updated | Security scan |
| DS-3 | `database` | PR with migration files | Filters for `.sql`, `.prisma`, `drizzle` |
| DS-4 | `qa-tester` + `workflow-qa-e2e` | Merge to develop | Reviews test report |
| DS-5 | `deployment` + `workflow-deploy` | Promote to production | Reviews release notes |
| DS-6 | `security` | Cron (Mon 9am) | Polls DB for repos due; saves results |
| DS-7 | `monitoring` | Post-deploy webhook | Analyzes health report / metrics |

---

### 5. Notification Sub-Workflow

`Notify: Google Chat` is data-driven — it does **not** have hardcoded webhook URLs. Instead:
1. Receives `channel`, `message`, `title`, `severity`, `details[]` as input
2. Queries `notification_channels` table for the webhook URL by channel name
3. Guards against unconfigured channels (checks for placeholder value `REPLACE_WITH_WEBHOOK_URL`)
4. Builds either a plain text message or a **Google Chat Cards v2** structured card (with header, body sections, action button)
5. Posts via HTTP with 10s timeout

Severity levels: `critical` (red), `high` (orange), `warning` (yellow), `info` (blue), `success` (green)

---

## Strengths

### 1. Consistent Auth Pattern
Every guarded endpoint calls Auth Guard as the first node. The sub-workflow returns a normalized auth object, and every parent workflow performs `IF authenticated?` before proceeding. The pattern is copy-consistent across 20+ workflows.

### 2. Reusable Sub-Workflows
Both Auth Guard and Google Chat are proper sub-workflows rather than duplicated logic. Google Chat's DB-driven webhook URL lookup means adding a new notification channel requires only a DB row, not a workflow change.

### 3. Retry Loop in Design-to-Code
The Nexus pipeline implements a `_retry_count` counter with a max of 3 retries for validation failures, resetting between validation → fix → re-validate cycles. Error propagation through `onError: continueErrorOutput` feeds into the Error Handler workflow.

### 4. Centralized Error Handler
`IYX78duIffflObuQ` is registered as `errorWorkflow` in all DS workflows. It extracts the project name from execution data, updates the DB status to `failed`, and notifies Google Chat with the error message — all without each workflow needing its own error handling.

### 5. Fix Prompt Base64 Encoding
In `Nexus Design-to-Code`, the validation error list is base64-encoded before being passed to the shell command. This prevents special characters in error messages from breaking the shell command or causing injection.

### 6. PDF Validation Before Processing
Step 2 validates MIME type, file extension, and file size before uploading or processing. Invalid/oversized files are rejected immediately with a structured error response.

### 7. Session Security
Login sets `HttpOnly; Secure; SameSite=Strict` cookie. Logout clears it with `Max-Age=0`. Session validation uses a parameterized SQL query with a JOIN that also checks `user.status = 'active'`.

---

## Issues & Security Concerns

### CRITICAL

#### 1. SQL Injection in Multiple Workflows
Several Postgres nodes use n8n template interpolation directly in SQL strings instead of parameterized queries:

| Workflow | Node | Vulnerable Field |
|----------|------|-----------------|
| `Step 2: PRD Generation` | Lookup Project Registry | `project_name` |
| `Approve PRD` | Lookup Project | `project_name` |
| `Get Nexus Job Status` | Get Job Status | `projectName` (URL param) |
| `User Management: Invite User` | Insert User to DB | `email`, `name`, `invited_by` |
| `DS-6: Weekly Audit` | Save Audit to DB | `repo`, `findings` |
| `Notify: Google Chat` | Get Webhook URL | `channel` |

The pattern `WHERE column = '{{ $json.value }}'` is classic SQL injection. `Auth: Validate Session` correctly uses `$1`, but this is not applied consistently.

**Fix**: Use n8n's `Query Parameters` / `queryReplacement` option on all Postgres nodes, or use the parameterized `$1, $2...` syntax.

#### 2. `User Management: Invite User` Has No Auth Guard
The Invite User workflow goes directly from Webhook → Setup Invite Data → DB Insert — there is **no Auth Guard call**. Anyone who can reach `POST /ai-project/v1/users/invite` can insert arbitrary users into the database.

#### 3. `Approve PRD` Has No Auth Guard
`Approve PRD` starts with a Webhook and immediately extracts `projectName` from the body, then queries the DB — no authentication check. Any unauthenticated caller can approve a PRD.

---

### HIGH

#### 4. Hardcoded Internal IP in Nexus Design-to-Code
`Nexus Design-to-Code` hardcodes `http://10.0.11.1:3900/mcp` as the MCP server endpoint. The DS-1 through DS-7 workflows use `http://localhost:3900/mcp`. These are inconsistent — one uses an internal LAN IP, the other assumes the MCP server runs on the same host as n8n. Neither is configurable without editing the workflow JSON.

**Fix**: Store the MCP server URL in an n8n environment variable (`$env.NEXUS_MCP_URL`) and reference it in both places.

#### 5. Google Chat Notification ID Is a Placeholder in DS Workflows
DS-1 through DS-7 all reference `"notifyGoogleChatWorkflowId"` as the `workflowId` for the Notify Google Chat node. This is a **placeholder string** — the actual workflow ID is `G2SEoq84kLWf054f`. The DS workflows will fail silently at the notification step until this is corrected.

#### 6. All DS Workflows Are Inactive (`"active": false`)
None of the 7 DevSecOps automation workflows are active. They need to be enabled and have their webhook/cron triggers registered before any CI/CD integration will work.

#### 7. DS-6 Manual SQL Escaping Is Unreliable
`DS-6: Weekly Audit` attempts to escape findings for insertion with `$json.findings.replace(/'/g, "''")`. This is DIY escaping that:
- Only escapes single quotes (misses other injection vectors)
- Throws a TypeError if `findings` is not a string (e.g., if Claude returns a JSON object)

---

### MEDIUM

#### 8. Step 3 Heredoc Without Encoding Can Break
`Step 3: Dev Tasks Generation` passes `extractEpicsPrompt` into a shell heredoc (`cat << 'EOF' | claude ...`). The single-quoted `'EOF'` delimiter prevents variable expansion, but if the prompt contains the literal string `EOF` on its own line, the heredoc terminates early. This is a subtle content-dependent failure mode.

**Fix**: Use base64 encoding like `Nexus Design-to-Code` does in its fix prompt.

#### 9. Error Handler Race Condition
`Error Handler - Update Failed Status` updates the project with status `'failed'` by selecting **the most recently started project with status `'processing'`** — not the specific project that failed:
```sql
WHERE workflow_status = 'processing'
ORDER BY workflow_started_at DESC LIMIT 1
```
If two pipeline runs fail simultaneously, the wrong project could be marked as failed.

**Fix**: Pass the project name through the n8n execution context so the error handler can update the correct row directly.

#### 10. Fallback Epics in Step 3 Silently Continue
When Claude fails to return parseable JSON for epic extraction, `Parse Epics Response` falls back to 3 hardcoded generic epics (`Core Features`, `User Management`, `Integration & Deployment`) and continues the workflow. This means task generation can proceed on entirely wrong epics with no alert to the user.

**Fix**: Throw an error and surface it to the user instead of silently using stale generic data.

#### 11. No Rate Limiting on Auth Endpoints
Login, invite, and other auth endpoints have no rate limiting, lockout, or brute-force protection. An attacker can enumerate valid `@stratpoint.com` addresses or attempt API key brute force.

#### 12. `Restore Binary After DB` Pattern Is Fragile
Step 2 uses a dedicated `Restore Binary After DB` Code node after every Postgres query to re-attach the PDF binary data. This is a workaround for n8n data flow behavior. If any refactoring moves or adds a Postgres node, the binary reference will break silently.

---

### LOW

#### 13. Step 1 Auth Relies Only on `X-User-Email` Header
`Step 1: Project Setup` reads `createdBy` from `headers['x-user-email']` rather than going through a full Auth Guard call. This means the `createdBy` field in the DB can be set to any value by the caller.

#### 14. DS-3 Migration File Filter Is Brittle
DS-3 checks for migration files by looking for strings like `"migration"`, `"prisma/schema"`, `".sql"`, `"drizzle"` in `changed_files`. This is string-based and will miss:
- Files in `db/` directories without "migration" in the name
- Files with `.ts` ORM migration extensions

#### 15. Notification Channel Hardcoded Strings Across Workflows
Notification channel names (`'devsecops-reviews'`, `'ai-workflow-manager'`) are string literals scattered across multiple workflows. If a channel is renamed in the DB, all workflows must be updated individually.

---

## Summary Ratings

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Auth Architecture | ★★★★☆ | Consistent Auth Guard pattern; missing on 2 workflows |
| Security | ★★☆☆☆ | SQL injection in 6+ workflows; 2 unguarded endpoints |
| Code Quality | ★★★☆☆ | Good sub-workflow reuse; some fragile patterns |
| Reliability | ★★★☆☆ | Retry logic in pipeline; race condition in error handler |
| Observability | ★★★★☆ | Centralized error handler + Google Chat notifications |
| Configurability | ★★☆☆☆ | Hardcoded IPs, placeholder workflow IDs, DB-bound channel names |
| DevSecOps Readiness | ★★☆☆☆ | All DS workflows inactive; notification ID is a placeholder |

---

## Top Recommendations (Priority Order)

1. **Fix SQL injection in all 6+ Postgres nodes** — replace `'{{ $json.value }}'` interpolation with n8n's `Query Parameters` / parameterized `$1` syntax. This is the most critical security gap.

2. **Add Auth Guard to `Invite User` and `Approve PRD`** — these endpoints mutate data (user creation, PRD approval) without any authentication check.

3. **Replace the `notifyGoogleChatWorkflowId` placeholder** in DS-1 through DS-7 with the real workflow ID `G2SEoq84kLWf054f`, then activate the DS workflows.

4. **Move the MCP server URL to an n8n environment variable** (`$env.NEXUS_MCP_URL`) to eliminate the `10.0.11.1` vs `localhost` inconsistency and make the cluster address configurable.

5. **Fix the Error Handler race condition** — pass `projectName` through the n8n execution context using a [Custom Error Data](https://docs.n8n.io/flow-logic/error-handling/) payload, then update by `project_name` in the error handler SQL.

6. **Base64-encode the epics prompt in Step 3** (like `Nexus Design-to-Code` does for fix prompts) to prevent heredoc injection on content-containing `EOF` lines.

7. **Surface the fallback epic failure** — replace the silent generic-epics fallback with a thrown error and a 422 response so users know task generation failed rather than silently generating meaningless tasks.
