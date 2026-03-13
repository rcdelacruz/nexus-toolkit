"""
Persistent file-based memory for dev-workflow agents.

Memory lives in the developer's project (not nexus-mcp):

  Solo:
    {memory_dir}/{agent_name}.md

  Team (two-layer):
    {memory_dir}/shared/{agent_name}.md   ← git-committed, team-owned
    {memory_dir}/personal/{agent_name}.md ← gitignored, per-developer

All writes target personal/ (or flat) by default. Devs promote curated
findings to shared/ manually via git. shared/ is loaded first so personal/
context takes precedence when merged into the context block.
"""

from __future__ import annotations

import pathlib
import re
from datetime import date

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_RECENT_FINDINGS = 3

_REVIEW_TRIGGERS: list[str] = [
    "migrate",
    "migration",
    "architectural change",
    "major refactor",
    "breaking change",
    "remove",
    "deprecate",
    "replace",
    "switch from",
    "switch to",
    "upgrade major",
    "downgrade",
    "rewrite",
    "extract service",
    "split",
    "decompose",
    "security architecture",
    "abandon",
    "drop support",
]

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

_BLANK_TEMPLATE = """\
---
name: {agent_name} memory
description: Persistent findings from {agent_name} for this project
type: agent-memory
agent: {agent_name}
project: {project_name}
created: {today}
last_updated: {today}
run_count: 0
---

## Architecture Decisions

## Recurring Issues

## Resolved

## Recent Findings

## ⚠️ Pending Human Review
"""

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_paths(memory_dir: str, agent_name: str) -> tuple[pathlib.Path | None, pathlib.Path]:
    """Return (read_shared_path_or_None, write_personal_path).

    Resolution:
      - shared  : {memory_dir}/shared/{agent_name}.md  (read only, may not exist)
      - personal: {memory_dir}/personal/{agent_name}.md (read+write)
      - solo    : {memory_dir}/{agent_name}.md          (flat, no subdirs)

    If neither shared/ nor personal/ dirs exist and the flat file exists → solo mode.
    If neither shared/ nor personal/ dirs exist and the flat file does NOT exist → create personal/.
    """
    base = pathlib.Path(memory_dir)
    shared_dir = base / "shared"
    personal_dir = base / "personal"
    flat_file = base / f"{agent_name}.md"

    shared_file = shared_dir / f"{agent_name}.md"
    personal_file = personal_dir / f"{agent_name}.md"

    # If the flat file exists and no layer dirs exist → solo mode
    if flat_file.exists() and not shared_dir.exists() and not personal_dir.exists():
        return None, flat_file

    # If explicitly in solo mode (no subdirs ever existed, nothing yet)
    if not shared_dir.exists() and not personal_dir.exists() and not flat_file.exists():
        # Default to personal/ (team-ready from day one)
        return None, personal_file

    # Two-layer mode
    shared = shared_file if shared_file.exists() else None
    return shared, personal_file


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split YAML frontmatter from body. Returns ({key: value}, body)."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()

    body = text[m.end():]
    return fm, body


def _render_frontmatter(fm: dict[str, str]) -> str:
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _section_content(body: str, section: str) -> str:
    """Extract content under a ## section header."""
    pattern = re.compile(
        r"^## " + re.escape(section) + r"\s*\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else ""


def _replace_section(body: str, section: str, new_content: str) -> str:
    """Replace the content under a ## section header."""
    pattern = re.compile(
        r"(^## " + re.escape(section) + r"\s*\n)(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    replacement = f"\\1{new_content}\n\n" if new_content else "\\1\n"
    result, count = pattern.subn(replacement, body)
    if count == 0:
        # Section missing — append it
        result = body.rstrip() + f"\n\n## {section}\n\n{new_content}\n"
    return result


def _key80(text: str) -> str:
    """Normalised 80-char dedup key."""
    return re.sub(r"\s+", " ", text.strip().lower())[:80]


def _scan_triggers(text: str) -> list[str]:
    """Return sentences/lines that contain review trigger keywords."""
    hits: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        low = line.lower()
        for trigger in _REVIEW_TRIGGERS:
            if trigger in low:
                key = _key80(line)
                if key not in seen:
                    seen.add(key)
                    # Trim to a reasonable length
                    snippet = line.strip()[:120]
                    hits.append(snippet)
                break
    return hits


def _auto_gitignore(personal_dir: pathlib.Path) -> None:
    """Append gitignore entry for personal/ when creating it for the first time.

    Walks up from personal_dir to find the project root (.git), then appends
    to .gitignore if the entry isn't already present.
    """
    try:
        # Find project root (up to 5 levels)
        root: pathlib.Path | None = None
        candidate = personal_dir.parent
        for _ in range(5):
            if (candidate / ".git").exists():
                root = candidate
                break
            parent = candidate.parent
            if parent == candidate:
                break
            candidate = parent

        if root is None:
            return  # Not inside a git repo — skip silently

        gitignore = root / ".gitignore"
        # Relative path from project root
        try:
            rel = str(personal_dir.relative_to(root)).replace("\\", "/")
        except ValueError:
            rel = ".claude/memory/agents/personal/"
        entry = rel.rstrip("/") + "/"

        existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        if entry not in existing and entry.rstrip("/") not in existing:
            with gitignore.open("a", encoding="utf-8") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write(f"\n# nexus agent personal memory (per-developer, not shared)\n{entry}\n")
    except Exception:
        pass  # Never raise — gitignore update is best-effort


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_memory(memory_dir: str, agent_name: str) -> str | None:
    """Return raw file text for agent memory, or None if no file exists. Never raises."""
    try:
        shared, personal = _resolve_paths(memory_dir, agent_name)
        parts: list[str] = []
        if shared and shared.exists():
            parts.append(shared.read_text(encoding="utf-8"))
        if personal.exists():
            parts.append(personal.read_text(encoding="utf-8"))
        return "\n\n".join(parts) if parts else None
    except Exception:
        return None


def update_memory(
    memory_dir: str,
    agent_name: str,
    findings_text: str,
    mode: str = "append",
    project_name: str = "",
) -> tuple[bool, list[str]]:
    """Write agent findings into memory file.

    Args:
        memory_dir: Path to the agents/ directory.
        agent_name: Name of the agent.
        findings_text: Raw output from the agent run.
        mode: "append" | "replace" | "reset"
        project_name: Used when creating a new memory file.

    Returns:
        (success, pending_items_added_this_run)
    """
    try:
        _, write_path = _resolve_paths(memory_dir, agent_name)
        is_personal = write_path.parent.name == "personal"
        today = date.today().isoformat()
        new_pending: list[str] = []

        # Auto-gitignore on first personal/ creation
        if is_personal and not write_path.parent.exists():
            _auto_gitignore(write_path.parent)

        write_path.parent.mkdir(parents=True, exist_ok=True)

        # ── Build or load existing file ────────────────────────────────────
        if write_path.exists():
            raw = write_path.read_text(encoding="utf-8")
            fm, body = _parse_frontmatter(raw)
            if not fm:
                # Corrupt or plain file — rebuild template
                fm = {
                    "name": f"{agent_name} memory",
                    "description": f"Persistent findings from {agent_name} for this project",
                    "type": "agent-memory",
                    "agent": agent_name,
                    "project": project_name,
                    "created": today,
                    "last_updated": today,
                    "run_count": "0",
                }
                body = _build_blank_body()
        else:
            fm = {
                "name": f"{agent_name} memory",
                "description": f"Persistent findings from {agent_name} for this project",
                "type": "agent-memory",
                "agent": agent_name,
                "project": project_name,
                "created": today,
                "last_updated": today,
                "run_count": "0",
            }
            body = _build_blank_body()

        # ── Apply mode ──────────────────────────────────────────────────────
        if mode == "reset":
            fm["run_count"] = "0"
            fm["last_updated"] = today
            body = _build_blank_body()

        elif mode == "replace":
            fm["last_updated"] = today
            try:
                run_count = int(fm.get("run_count", "0")) + 1
            except ValueError:
                run_count = 1
            fm["run_count"] = str(run_count)
            body = findings_text

        else:  # append (default)
            try:
                run_count = int(fm.get("run_count", "0")) + 1
            except ValueError:
                run_count = 1
            fm["run_count"] = str(run_count)
            fm["last_updated"] = today

            # 1. Trigger detection → ⚠️ Pending Human Review
            triggered = _scan_triggers(findings_text)
            if triggered:
                existing_pending = _section_content(body, "⚠️ Pending Human Review")
                # Extract content keys from existing items, stripping - [ ] prefix and — flagged suffix
                _pending_content_re = re.compile(r"^- \[[ x]\] (.+?)(?:\s+—\s+flagged .+)?$")
                existing_keys: set[str] = set()
                for line in existing_pending.splitlines():
                    pm = _pending_content_re.match(line.strip())
                    if pm:
                        existing_keys.add(_key80(pm.group(1)))
                    elif line.strip():
                        existing_keys.add(_key80(line))
                for snippet in triggered:
                    key = _key80(snippet)
                    if key not in existing_keys:
                        item = f"- [ ] {snippet} — flagged {today}"
                        new_pending.append(item)
                        existing_keys.add(key)

                if new_pending:
                    updated_pending = (
                        (existing_pending + "\n" if existing_pending else "")
                        + "\n".join(new_pending)
                    ).strip()
                    body = _replace_section(body, "⚠️ Pending Human Review", updated_pending)

            # 2. Recurring Issues — count repeated patterns
            top_lines = [
                l.strip() for l in findings_text.splitlines()
                if l.strip() and not l.startswith("#") and len(l.strip()) > 20
            ][:5]
            if top_lines:
                existing_issues = _section_content(body, "Recurring Issues")
                issue_lines = existing_issues.splitlines() if existing_issues else []
                issue_map: dict[str, int] = {}
                count_re = re.compile(r"^- \((\d+)x\) (.+)$")
                for line in issue_lines:
                    m = count_re.match(line)
                    if m:
                        issue_map[_key80(m.group(2))] = int(m.group(1))

                for line in top_lines:
                    k = _key80(line)
                    if k in issue_map:
                        issue_map[k] += 1

                # Rebuild the issue list with updated counts
                updated_lines: list[str] = []
                for line in issue_lines:
                    m2 = count_re.match(line)
                    if m2:
                        key = _key80(m2.group(2))
                        cnt = issue_map.get(key, int(m2.group(1)))
                        updated_lines.append(f"- ({cnt}x) {m2.group(2)}")
                updated_issues = "\n".join(updated_lines) if updated_lines else existing_issues
                if updated_issues != existing_issues and updated_issues:
                    body = _replace_section(body, "Recurring Issues", updated_issues)

            # 3. Recent Findings — rolling window of _MAX_RECENT_FINDINGS
            summary_line = _first_meaningful_line(findings_text)
            if summary_line:
                existing_recent = _section_content(body, "Recent Findings")
                recent_lines = [l for l in existing_recent.splitlines() if l.strip()]
                # Prepend newest, drop oldest
                new_entry = f"- [{today}] (run #{run_count}) {summary_line}"
                recent_lines = [new_entry] + recent_lines
                recent_lines = recent_lines[:_MAX_RECENT_FINDINGS]
                body = _replace_section(body, "Recent Findings", "\n".join(recent_lines))

        # ── Atomic write ────────────────────────────────────────────────────
        output = _render_frontmatter(fm) + "\n" + body.lstrip("\n")
        tmp = write_path.with_suffix(".tmp")
        tmp.write_text(output, encoding="utf-8")
        tmp.replace(write_path)

        return True, new_pending

    except Exception as exc:
        return False, []


def build_memory_context_block(memory_dir: str, agent_name: str) -> str:
    """Build a context block to prepend to user_message before an agent run.

    Loads shared/{agent_name}.md (team layer) then personal/{agent_name}.md
    (personal layer). Falls back to flat {agent_name}.md for solo projects.
    Returns "" if no memory files exist (first run — no error).
    """
    try:
        shared, personal = _resolve_paths(memory_dir, agent_name)
        parts: list[str] = []

        if shared and shared.exists():
            _, body = _parse_frontmatter(shared.read_text(encoding="utf-8"))
            body = body.strip()
            if body:
                parts.append(f"### Shared team memory\n\n{body}")

        if personal.exists():
            _, body = _parse_frontmatter(personal.read_text(encoding="utf-8"))
            body = body.strip()
            if body:
                parts.append(f"### Personal memory\n\n{body}")

        if not parts:
            return ""

        combined = "\n\n---\n\n".join(parts)
        return (
            f"## Past Memory ({agent_name})\n\n"
            f"{combined}\n\n"
            f"---\n\n"
            f"(End of past memory — analyze the current context below)\n\n"
        )
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Internal helpers (continued)
# ---------------------------------------------------------------------------


def _build_blank_body() -> str:
    return (
        "## Architecture Decisions\n\n"
        "## Recurring Issues\n\n"
        "## Resolved\n\n"
        "## Recent Findings\n\n"
        "## ⚠️ Pending Human Review\n"
    )


def _first_meaningful_line(text: str) -> str:
    """Return the first non-empty, non-header line from text, truncated to 120 chars."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and len(stripped) > 10:
            return stripped[:120]
    return ""
