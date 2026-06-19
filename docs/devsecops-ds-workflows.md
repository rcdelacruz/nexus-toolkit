# DevSecOps DS Workflows — Specification

**Status: Not started.** This document is the authoritative specification for DS-1 through DS-7.

---

## Architecture Overview

```
GitHub/GitLab PR webhook
        │
        ▼
  n8n DS Workflow
        │
        ├─► Auth Guard (Sub-Workflow)       — validates webhook signature / API key
        │
        ├─► Fetch context (PR diff, files)  — GitHub/GitLab API
        │
        ├─► Nexus MCP HTTP call             — routes to the right Claude Code agent
        │       └─► http://10.0.11.1:3900/mcp
        │
        ├─► Publish results                 — GitHub/GitLab API (comments, status, issues)
        │
        ├─► Notify: Google Chat             — via Notify sub-workflow
        │
        └─► Write to PostgreSQL             — devsecops_scans / deployments / security_audits
```

n8n handles orchestration: authentication, API calls, database writes, and notifications. Nexus MCP handles the analysis: it receives the diff or file list and routes to the appropriate Claude Code agent tool.

---

## Nexus MCP Server

### Connection details

| Property | Value |
|---|---|
| URL | `http://10.0.11.1:3900/mcp` |
| Protocol | HTTP (FastMCP) |
| Accessible from | Inside the Docker host via SSH, or directly from n8n containers |
| Process manager | systemd user service `nexus-sse` |
| Port | 3900 |
| Entry point | `nexus_server.py` |

### Current tools registered

- `nexus_search` / `nexus_read` — codebase search
- `ingest_figma_zip` / `ingest_from_prompt` / `ingest_from_codebase` — Design-to-Code pipeline ingestion
- `remap_to_golden_path` / `validate_output` / `package_output` / `update_file_in_tree` — pipeline steps
- `run_agent` — runs any dev-workflow agent (code-reviewer, security, database, qa-tester, deployment, monitoring, etc.)
- `get_agent_memory` / `update_agent_memory` — persistent agent memory

### DS workflows use `run_agent` — no new tools needed

All DS workflows call the existing `run_agent` tool. The 6 agent types already have full system prompts and handle the required analysis:

| DS workflow | Agent name passed to `run_agent` |
|---|---|
| DS-1 (Code Review) | `code-reviewer` |
| DS-2 (Security Scan) | `security` |
| DS-3 (Database Review) | `database` |
| DS-4 (QA Gate) | `qa-tester` |
| DS-5 (Deploy Review) | `deployment` |
| DS-7 (Health Check) | `monitoring` |

Do **not** create `tools/pr_reviewer.py`, `tools/security.py`, etc. — they are redundant.

### How to restart the server

```bash
ssh ronald@168.138.191.197 'systemctl --user restart nexus-sse'
```

### How to verify tools are registered

```bash
curl -s -X POST http://10.0.11.1:3900/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | python3 -m json.tool
```

### How n8n calls Nexus MCP

Use an HTTP Request node in n8n:

```
POST http://10.0.11.1:3900/mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "run_agent",
    "arguments": {
      "agent_name": "code-reviewer",
      "context": "{{ $json.prDiff }}"
    }
  }
}
```

The response is a JSON object. Parse `result.content[0].text` for the agent's findings.

---

## PostgreSQL Tables

All tables exist in the Neon DB after running `migrations/008_auth_and_devsecops.sql`. Do not re-create them.

### `monitored_repos`

Repos enrolled in the DevSecOps pipeline. DS-6 reads this table to know which repos to audit.

```sql
-- Enroll a repo
INSERT INTO monitored_repos (repo_url, repo_name, platform, default_branch)
VALUES ('https://github.com/stratpoint-engineering/my-repo', 'my-repo', 'github', 'main');
```

### `devsecops_scans`

PR scan results from DS-1, DS-2, DS-3, DS-4.

Columns: `id`, `repo_name`, `pr_number`, `scan_type` ('code_review' | 'security' | 'database' | 'qa'), `status` ('pass' | 'fail' | 'error'), `findings` (JSONB), `created_at`.

### `security_audits`

Weekly audit results from DS-6.

Columns: `id`, `repo_name`, `audit_date`, `findings` (JSONB), `report_drive_url`, `created_at`.

### `deployments`

Deployment tracking from DS-5 and DS-7.

Columns: `id`, `repo_name`, `environment` ('staging' | 'production'), `version`, `status` ('pending' | 'healthy' | 'unhealthy' | 'rolled_back'), `health_check_url`, `started_at`, `completed_at`, `created_at`.

---

## DS-1, DS-2, DS-3 — Shared PR Webhook

DS-1 (Code Review), DS-2 (Security Scan), and DS-3 (Database Review) all trigger from the same PR webhook. Build these as a single n8n workflow with a fan-out pattern.

```
Webhook Trigger (GitHub/GitLab PR event)
  └─► Auth Guard
        └─► IF Authenticated?
              ├─ FALSE → Respond 401
              └─ TRUE
                    └─► Parse PR metadata (repo, PR number, branch, changed files)
                          └─► Fetch PR diff (GitHub API)
                                ├─► Branch A: DS-1 Code Review
                                ├─► Branch B: DS-2 Security Scan
                                └─► Branch C: DS-3 Database Review (conditional)
```

All three branches write to `devsecops_scans` independently. Branches run in parallel — do not chain them sequentially.

---

## DS-1 — PR Code Review

### Summary

Posts AI code review comments on GitHub/GitLab pull requests. Advisory only — does not block merge.

### Trigger

GitHub webhook event: `pull_request` with actions `opened` and `synchronize`.

GitLab webhook event: `Merge Request Hook` with state `opened`.

### Authentication

GitHub: Validate `X-Hub-Signature-256` HMAC using the webhook secret stored in n8n credentials.

GitLab: Validate `X-Gitlab-Token` header against the token stored in n8n credentials.

### Process

1. Extract: PR number, repo full name, head SHA, base SHA, branch name.
2. Fetch PR diff: `GET https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}` with `Accept: application/vnd.github.v3.diff`.
3. Call Nexus MCP `run_agent` with agent `code-reviewer`:
   ```json
   {
     "jsonrpc": "2.0", "id": 1,
     "method": "tools/call",
     "params": {
       "name": "run_agent",
       "arguments": {
         "agent_name": "code-reviewer",
         "context": "PR: <pr_title>\n\n<pr_description>\n\nDiff:\n<raw diff string>"
       }
     }
   }
   ```
4. Parse findings from MCP response.
5. Post review comments to GitHub:
   - `POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews`
   - `event: COMMENT` (not APPROVE or REQUEST_CHANGES — advisory only)
   - Include inline comments on specific diff lines where possible.
6. Write to `devsecops_scans`: `scan_type = 'code_review'`, `status = 'pass'`, `findings = <MCP JSON output>`.
7. Notify `#devsecops-reviews` via Google Chat sub-workflow.

### Output

- PR review comment thread on GitHub/GitLab
- Google Chat message in `#devsecops-reviews`
- Row in `devsecops_scans`

### Blocking

No. Posts comments only.

### Google Chat message template

```
*PR Code Review Complete*
Repo: {repo_name} | PR #{pr_number}
Findings: {finding_count} suggestions
[View PR]({pr_url})
```

---

## DS-2 — Security Scan

### Summary

Scans PR diff for security vulnerabilities (OWASP Top 10, hardcoded secrets, auth bypasses). Blocks merge on Critical or High severity findings by setting a failed GitHub commit status.

### Trigger

Same PR webhook as DS-1 (runs as a parallel branch).

### Authentication

Same as DS-1 — GitHub HMAC or GitLab token.

### Process

1. Reuse PR diff fetched in the shared webhook handler (passed from the Parse PR metadata node).
2. Call Nexus MCP `run_agent` with agent `security`:
   ```json
   {
     "jsonrpc": "2.0", "id": 1,
     "method": "tools/call",
     "params": {
       "name": "run_agent",
       "arguments": {
         "agent_name": "security",
         "context": "Security scan request. Scan categories: OWASP Top 10, hardcoded secrets, auth bypass, injection.\n\nDiff:\n<raw diff string>"
       }
     }
   }
   ```
3. Parse findings. Determine highest severity in the response.
4. Set GitHub commit status:
   - `POST /repos/{owner}/{repo}/statuses/{sha}`
   - If Critical or High finding: `state: failure`, `description: "Security issues found — merge blocked"`
   - Otherwise: `state: success`, `description: "No critical security issues found"`
   - `context: "nexus/security-scan"`
5. Write to `devsecops_scans`: `scan_type = 'security'`, `status = 'pass'` or `'fail'`.
6. Notify `#security-alerts` via Google Chat sub-workflow.

### Output

- GitHub commit status (visible in PR merge checks)
- Google Chat message in `#security-alerts`
- Row in `devsecops_scans`

### Blocking

**Yes — blocks merge if highest severity is Critical or High.** GitHub branch protection rules must be configured to require the `nexus/security-scan` status check to pass.

### Google Chat message template (on failure)

```
*Security Scan FAILED*
Repo: {repo_name} | PR #{pr_number}
Severity: {highest_severity}
Findings: {critical_count} critical, {high_count} high
Merge is blocked. [View PR]({pr_url})
```

---

## DS-3 — Database Review

### Summary

Reviews SQL migrations and ORM schema changes for destructive operations (DROP TABLE, DROP COLUMN, non-reversible ALTER). Blocks merge if a destructive operation has no corresponding down migration.

### Trigger

Same PR webhook as DS-1. This branch runs conditionally.

### Authentication

Same as DS-1 — GitHub HMAC or GitLab token.

### Conditional execution

Only run if the PR touches files matching:

- `*.sql`
- `prisma/schema*`
- `drizzle/**`
- `migrations/**`

Use an IF node after "Parse PR metadata": check `changedFiles` list against these patterns. If no match, skip this branch entirely (no DB write, no notification).

### Process

1. Extract the content of changed migration files from the PR:
   - `GET /repos/{owner}/{repo}/contents/{file_path}?ref={head_sha}` for each matched file.
2. Call Nexus MCP `run_agent` with agent `database`:
   ```json
   {
     "jsonrpc": "2.0", "id": 1,
     "method": "tools/call",
     "params": {
       "name": "run_agent",
       "arguments": {
         "agent_name": "database",
         "context": "Database migration review. Check for destructive operations (DROP TABLE, DROP COLUMN, irreversible ALTER) without corresponding down migrations.\n\nChanged migration files:\n<file path and content for each matched file>"
       }
     }
   }
   ```
3. Parse the response. Check if any finding has `requires_rollback: true` and no down migration is present.
4. Post a PR comment with the findings summary.
5. If blocking condition met: set GitHub commit status `failure` with `context: "nexus/database-review"`.
6. Write to `devsecops_scans`: `scan_type = 'database'`, `status = 'pass'` or `'fail'`.
7. Notify `#devsecops-reviews` via Google Chat sub-workflow.

### Output

- PR comment with findings
- GitHub commit status (conditional)
- Google Chat message in `#devsecops-reviews`
- Row in `devsecops_scans`

### Blocking

Conditional — blocks merge only when a DROP TABLE, DROP COLUMN, or irreversible data-loss operation is present without a corresponding down migration or backup step.

---

## DS-4 — QA Gate

### Summary

After a PR is merged to the develop branch, analyzes the merged diff for test coverage gaps and creates a GitHub Issue listing recommended tests.

### Trigger

GitHub webhook event: `push` on branch `develop` (or the repo's integration branch).

This is a separate webhook from DS-1/2/3. Build as a standalone n8n workflow.

### Authentication

GitHub HMAC (`X-Hub-Signature-256`).

### Process

1. Extract: before SHA, after SHA, pushed commits, repo name.
2. Fetch the diff of the push:
   - `GET /repos/{owner}/{repo}/compare/{before}...{after}`
3. Call Nexus MCP `run_agent` with agent `qa-tester`:
   ```json
   {
     "jsonrpc": "2.0", "id": 1,
     "method": "tools/call",
     "params": {
       "name": "run_agent",
       "arguments": {
         "agent_name": "qa-tester",
         "context": "QA analysis for push to develop branch. Identify test coverage gaps and recommend test cases.\n\nChanged files: <list>\n\nDiff:\n<raw diff string>"
       }
     }
   }
   ```
4. Parse the response. Extract recommended test cases.
5. Create a GitHub Issue:
   - `POST /repos/{owner}/{repo}/issues`
   - Title: `[QA Gate] Test coverage gaps — {branch} push {short_sha}`
   - Body: formatted Markdown from MCP response
   - Labels: `qa`, `automated`
6. Write to `devsecops_scans`: `scan_type = 'qa'`, `status = 'pass'`.
7. Notify `#qa-alerts` via Google Chat sub-workflow.

### Output

- GitHub Issue with test recommendations
- Google Chat message in `#qa-alerts`
- Row in `devsecops_scans`

### Blocking

No. Advisory only.

### Google Chat message template

```
*QA Gate Analysis*
Repo: {repo_name} | Branch: develop
Commit: {short_sha}
Gaps identified: {gap_count}
[View Issue]({issue_url})
```

---

## DS-5 — Production Deploy Review

### Summary

When a GitHub release is created, fetches the release diff (focusing on infrastructure files) and generates a pre-deploy checklist with rollback procedures.

### Trigger

GitHub webhook event: `release` with action `published`.

Build as a standalone n8n workflow.

### Authentication

API key (`x-api-key` header). The GitHub webhook secret is sent as the API key. Validated by Auth Guard.

### Process

1. Extract: release tag, release name, release body, repo name.
2. Fetch the diff between the new tag and the previous tag:
   - `GET /repos/{owner}/{repo}/compare/{previous_tag}...{new_tag}`
3. Filter changed files to infrastructure-relevant patterns:
   - `*.tf`, `Dockerfile*`, `docker-compose*.yml`, `k8s/**`, `.github/workflows/**`
4. Call Nexus MCP `run_agent` with agent `deployment`:
   ```json
   {
     "jsonrpc": "2.0", "id": 1,
     "method": "tools/call",
     "params": {
       "name": "run_agent",
       "arguments": {
         "agent_name": "deployment",
         "context": "Pre-deploy review for release <tag>. Generate a deploy checklist and rollback procedures.\n\nChanged infrastructure files: <list>\n\nDiff:\n<filtered diff string>"
       }
     }
   }
   ```
5. Parse the response. Extract checklist and rollback steps.
6. Post a comment on the GitHub release:
   - `POST /repos/{owner}/{repo}/releases/{release_id}` (PATCH to add body content)
   - Or use the Releases API to post a release asset/comment.
7. Write to `deployments`: `environment = 'production'`, `version = release_tag`, `status = 'pending'`.
8. Notify `#deployments` via Google Chat sub-workflow.

### Output

- Comment on GitHub release with pre-deploy checklist
- Google Chat message in `#deployments`
- Row in `deployments`

### Blocking

No. Advisory only.

---

## DS-6 — Weekly Security Audit

### Summary

Every Monday at 9am, SSH into the server, clone all repos in `monitored_repos`, and run a consolidated security audit using Claude Code with Read and Bash tools only. Saves the report to Google Drive. Notifies `#security-alerts` and sends email.

### Trigger

n8n Cron node: `0 9 * * 1` (Monday 9:00am server time).

Build as a standalone n8n workflow.

### Authentication

None — internal cron trigger. No webhook involved.

!!! note "DS-6 is a separate standalone process"
    DS-6 n8n workflow is intentionally thin — it only triggers the external audit script, collects the report from stdout, saves to DB, and notifies. All audit logic lives in `/home/ronald/scripts/weekly-security-audit.sh` (or equivalent), which is maintained independently.

    The external script handles: repo cloning, running audit tools (npm audit, OWASP, secrets scan), and calling Claude Code or Nexus MCP for analysis and **security compliance report generation**. Claude Code / MCP is used specifically for the analysis + report generation step — turning raw audit tool outputs into structured Markdown compliance reports.

    n8n does not orchestrate the individual audit steps. The script is the audit engine; n8n is the scheduler and notifier.

!!! note "Google Drive integration (TODO)"
    The external script should output two things to stdout: the Markdown report body and the Google Drive file URL (after uploading). The `Parse Audit Output` n8n node should be updated to extract both, and `Save Audit to DB` should populate `report_file_id` and `report_url` columns in `security_audits`. These columns exist in the schema (`008_auth_and_devsecops.sql`) but are not yet wired in the workflow.

### Process

1. n8n fetches `monitored_repos`: `SELECT repo_name, platform FROM monitored_repos WHERE is_active = true`.
2. n8n passes repo list (base64-encoded JSON) to external script via SSH stdin.
3. External script (`/home/ronald/scripts/weekly-security-audit.sh`) handles:
   a. Derive repo URL from `repo_name` + `platform` (e.g. `https://github.com/{repo_name}`)
   b. `git clone --depth=1 {url} /tmp/audit/{repo_name}` (or `git pull` if already cloned)
   c. Run audit tools per repo — each tool is a separate bash script:
      - `npm audit --json` (if `package.json` present)
      - OWASP dependency check (if installed)
      - Secrets scan (`trufflehog` or `git secrets --scan`)
      - Additional audit scripts as needed
   d. Use Claude Code or Nexus MCP to analyze raw outputs and generate a consolidated **security compliance report** in Markdown
   e. Upload report to Google Drive and output the Drive URL
   f. Print the report + Drive URL to stdout (n8n collects this)
   g. Clean up: `rm -rf /tmp/audit/`
4. n8n writes to `security_audits`: `repo`, `audit_type`, `scan_date`, `findings`, `report_url`.
5. n8n notifies `#security-alerts` via Google Chat sub-workflow.
6. n8n sends email to security team with report link.

### Output

- Markdown report in Google Drive
- Google Chat message in `#security-alerts`
- Email to security team
- Row in `security_audits`

### Blocking

No. Report only.

### Google Chat message template

```
*Weekly Security Audit Complete*
Date: {audit_date}
Repos audited: {repo_count}
Critical: {critical_count} | High: {high_count}
[View Report in Drive]({drive_url})
```

---

## DS-7 — Health Check

### Summary

Called by the deploy pipeline after a deployment completes. Waits, then verifies the service is healthy. In staging, blocks promotion to production on failure. In production, triggers auto-rollback and notifies `#incidents` on failure.

### Trigger

Called by the deploy pipeline via HTTP request. Not a GitHub webhook.

- Endpoint: `POST /webhook/ai-project/v1/health-check`
- Auth: API key (`x-api-key` header)
- Body:
  ```json
  {
    "repo_name": "my-app",
    "environment": "staging",
    "version": "v1.2.3",
    "health_check_url": "https://staging.my-app.com/healthz",
    "services": ["api", "worker", "database"],
    "rollback_webhook": "https://deploy-system.internal/rollback"
  }
  ```

Build as a standalone n8n workflow.

### Authentication

API key (`x-api-key` header). Validated by Auth Guard.

### Process

1. Validate input. Write initial row to `deployments`: `status = 'pending'`.
2. Wait 2 minutes (n8n Wait node — `PT2M`).
3. Call `/healthz` endpoint: `GET {health_check_url}`.
   - Expect HTTP 200 with body `{ "status": "ok" }` (or similar).
4. If health check passes AND services list is provided, call Nexus MCP `run_agent` with agent `monitoring`:
   ```json
   {
     "jsonrpc": "2.0", "id": 1,
     "method": "tools/call",
     "params": {
       "name": "run_agent",
       "arguments": {
         "agent_name": "monitoring",
         "context": "Health check verification for <environment> deployment. Services: <list>. Verify monitoring coverage — are all services instrumented?\n\nHealth check response:\n<raw response body>"
       }
     }
   }
   ```
   The agent verifies monitoring coverage (are all services instrumented?).
5. Determine overall result: pass or fail.

**If pass:**
- Update `deployments`: `status = 'healthy'`, `completed_at = NOW()`.
- Respond `200 { "status": "healthy" }` to the deploy pipeline.
- Notify `#deployments` with a success message.

**If fail:**

- Update `deployments`: `status = 'unhealthy'`, `completed_at = NOW()`.
- If `environment == 'staging'`:
  - Respond `200 { "status": "unhealthy", "action": "promotion_blocked" }`.
  - Notify `#deployments`.
- If `environment == 'production'`:
  - Notify `#incidents` with high-severity alert.
  - Send email to on-call team.
  - Call `rollback_webhook` (POST with `{ "version": version, "reason": "health check failed" }`).
  - Respond `200 { "status": "unhealthy", "action": "rollback_triggered" }`.
  - Update `deployments`: `status = 'rolled_back'`.

### Output

- JSON response to deploy pipeline (pass/fail + action taken)
- Google Chat message in `#deployments` (pass) or `#incidents` (production failure)
- Email to on-call team (production failure only)
- Row in `deployments`

### Blocking

- **Staging**: yes — a non-healthy response causes the deploy pipeline to block promotion.
- **Production**: no blocking (already deployed), but triggers rollback.

---

## Build Order

Build in this sequence. Each step depends on the previous being stable.

```
Step 1  Verify Nexus MCP is ready — no new tools to build
        ├── Confirm run_agent is registered:
        │     curl -s -X POST http://10.0.11.1:3900/mcp \
        │       -H "Content-Type: application/json" \
        │       -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
        │       | python3 -m json.tool
        └── Smoke-test each agent used by DS workflows:
              nexus agent run code-reviewer "print('hello')"
              nexus agent run security "print('hello')"
              nexus agent run database "SELECT 1"
              nexus agent run qa-tester "function add(a,b){return a+b}"
              nexus agent run deployment "FROM node:20"
              nexus agent run monitoring "status: ok"

Step 2  Build DS-1/2/3 as single n8n workflow
        ├── Shared PR webhook + Auth Guard + PR diff fetch
        ├── Branch A: DS-1 code review → GitHub PR comment
        ├── Branch B: DS-2 security scan → GitHub commit status
        └── Branch C: DS-3 database review (conditional) → GitHub commit status + PR comment
        Test with a real GitHub PR (use a test repo)

Step 3  Build DS-4 (standalone workflow)
        ├── Push-to-develop webhook
        └── GitHub Issue creation
        Test by pushing to the develop branch of a test repo

Step 4  Build DS-5 (standalone workflow)
        ├── Release published webhook
        └── Release comment
        Test by creating a draft release on a test repo

Step 5  Build DS-7 (standalone workflow)
        ├── Triggered by API key POST
        ├── Wait → health check → Nexus MCP
        └── Respond with pass/fail + rollback trigger
        Test with curl, pointing at a real /healthz endpoint

Step 6  Build DS-6 (standalone cron workflow)
        ├── Cron → SSH → clone repos → audit → Claude Code report
        └── Upload to Drive + notify
        Test by triggering manually (disable cron, use manual trigger)

Step 7  Wire Phase 3 Google Chat notifications
        ├── Step 1 completion → #devsecops-reviews
        ├── Step 2 completion → #devsecops-reviews
        ├── Step 3 completion → #devsecops-reviews
        └── Approve PRD → #devsecops-reviews
        Prerequisite: update notification_channels with real Google Chat webhook URLs (notify workflow ID: G2SEoq84kLWf054f)
```

---

## Implementation Checklist

### Nexus MCP readiness (no new tools required)

- [ ] Confirm `run_agent` is registered: POST to `http://10.0.11.1:3900/mcp` with `tools/list`
- [ ] Smoke-test `code-reviewer`, `security`, `database`, `qa-tester`, `deployment`, `monitoring` agents
- [ ] Confirm `nexus-sse` systemd service is running: `ssh ronald@168.138.191.197 'systemctl --user status nexus-sse'`

### DS-1/2/3 n8n workflow

- [ ] Webhook node: GitHub `pull_request` event (opened, synchronize)
- [ ] Auth Guard wired (HMAC validation)
- [ ] Parse PR metadata node (repo, PR number, head SHA, changed files list)
- [ ] Fetch PR diff (GitHub API HTTP Request node)
- [ ] DS-1 branch: `run_agent(code-reviewer, <diff>)` → post GitHub PR review comments
- [ ] DS-2 branch: `run_agent(security, <diff>)` → set GitHub commit status (`nexus/security-scan`)
- [ ] DS-3 branch: IF changed files match SQL/Prisma/Drizzle patterns → fetch file contents → `run_agent(database, <content>)` → PR comment + conditional commit status
- [ ] All three branches write to `devsecops_scans`
- [ ] All three branches call Google Chat sub-workflow
- [ ] Webhook configured in GitHub repo settings (requires public URL — confirm n8n is accessible)
- [ ] Export updated workflow JSON and commit to `workflows/`

### DS-4 n8n workflow

- [ ] Webhook node: GitHub `push` event on `develop` branch
- [ ] Auth Guard wired (HMAC validation)
- [ ] Fetch push diff (GitHub compare API)
- [ ] `run_agent(qa-tester, <diff>)` call
- [ ] Create GitHub Issue with findings
- [ ] Write to `devsecops_scans`
- [ ] Notify `#qa-alerts`
- [ ] Export and commit workflow JSON

### DS-5 n8n workflow

- [ ] Webhook node: GitHub `release` event, action `published`
- [ ] Auth Guard wired (API key)
- [ ] Fetch release diff (compare previous tag to new tag)
- [ ] Filter to infrastructure files
- [ ] `run_agent(deployment, <diff>)` call
- [ ] Post checklist as release comment
- [ ] Write to `deployments`
- [ ] Notify `#deployments`
- [ ] Export and commit workflow JSON

### DS-7 n8n workflow

- [ ] Webhook node: POST `ai-project/v1/health-check`
- [ ] Auth Guard wired (API key)
- [ ] Write initial `deployments` row with `status = 'pending'`
- [ ] Wait node: 2 minutes
- [ ] HTTP health check GET `{health_check_url}`
- [ ] `run_agent(monitoring, <health_check_response>)` call (service monitoring coverage)
- [ ] IF pass: update deployments → respond 200 healthy → notify `#deployments`
- [ ] IF fail + staging: respond 200 promotion blocked → notify `#deployments`
- [ ] IF fail + production: notify `#incidents` + email + call rollback webhook → respond 200 rollback triggered
- [ ] Export and commit workflow JSON

### DS-6 n8n workflow

- [ ] Cron trigger node: `0 9 * * 1`
- [ ] Postgres node: fetch `monitored_repos`
- [ ] SSH node: clone repos + run `npm audit` + secrets scan for each repo
- [ ] SSH node: run Claude Code with `--allowedTools "Read,Bash"` to generate report
- [ ] Google Drive node: upload report Markdown file
- [ ] Write to `security_audits`
- [ ] Notify `#security-alerts`
- [ ] Send email (SMTP or Gmail node)
- [ ] SSH cleanup: `rm -rf /tmp/audit/`
- [ ] Test with manual trigger before activating cron
- [ ] Export and commit workflow JSON

### Prerequisites before starting

- [ ] Update `notification_channels` with real Google Chat webhook URLs for `security-alerts`, `deployments`, `qa-alerts`, `incidents` — Google Chat notify sub-workflow ID is `G2SEoq84kLWf054f`
- [ ] Confirm Nexus MCP server is running: `curl http://10.0.11.1:3900/mcp/tools/list`
- [ ] Confirm GitHub webhook secret is stored in n8n credentials
- [ ] Confirm GitHub API token (with `repo` scope) is stored in n8n credentials
- [ ] Configure GitHub branch protection rules to require `nexus/security-scan` status check on protected branches
- [ ] Enroll at least one repo in `monitored_repos` for DS-6 testing

---

## Common Pitfalls

**GitHub API rate limits:** The PR diff endpoint is not rate-limited heavily, but fetching individual file contents for DS-3 can exhaust limits on large PRs. Add `Accept: application/vnd.github.v3+json` and a GitHub App token (higher rate limit) rather than a personal access token.

**Diff size:** Very large PRs may produce diffs that exceed what Claude Code can process in a single context window. Truncate diffs to the most relevant changed files. The MCP tool should accept a `max_diff_bytes` argument.

**Nexus MCP cold start:** The FastMCP process may restart if the server reboots. Add a healthcheck to DS-7 that also verifies Nexus MCP is responding, and alert `#incidents` if it is down.

**n8n binary data in SSH nodes:** SSH nodes return stdout as binary data. Use a Code node after SSH nodes to extract the text: `$input.first().json.stdout` (or use `continueOnFail: true` and check for errors).

**Parallel branches and database writes:** When DS-1, DS-2, DS-3 run in parallel and all write to `devsecops_scans`, each branch must use its own Postgres node with its own `scan_type`. Do not share a single Postgres node across branches.
