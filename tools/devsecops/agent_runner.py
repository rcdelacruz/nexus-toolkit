import asyncio
import json
import logging
import pathlib
import shutil
import subprocess
from mcp.server.fastmcp import FastMCP

from tools.devsecops.memory import build_memory_context_block, update_memory

logger = logging.getLogger(__name__)

_NEXUS_ROOT = pathlib.Path(__file__).parent.parent.parent
_DEV_AGENTS_DIR = pathlib.Path(__file__).parent.parent / "dev-agents"

# Registry maps agent name → subdirectory within tools/dev-agents/
_AGENT_REGISTRY: dict[str, str] = {
    # cross-cutting
    "code-reviewer": "cross-cutting",
    "database": "cross-cutting",
    "deployment": "cross-cutting",
    "monitoring": "cross-cutting",
    "performance": "cross-cutting",
    "product-manager": "cross-cutting",
    "qa-tester": "cross-cutting",
    "security": "cross-cutting",
    "task-planner": "cross-cutting",
    "tech-writer": "cross-cutting",
    "test-planner": "cross-cutting",
    # architecture
    "software-architect": "architecture",
    "solution-architect": "architecture",
    "solution-designer": "architecture",
    # javascript
    "backend-api": "javascript",
    "frontend-ui": "javascript",
    "fullstack-nextjs": "javascript",
    "react-native": "javascript",
    # savants
    "savant-fullstack-js": "savants",
    "savant-flutter": "savants",
    "savant-java-spring": "savants",
    "savant-react-native": "savants",
}


def _load_dev_agent(agent_name: str) -> str:
    """Load agent markdown from tools/dev-agents/. Raises FileNotFoundError if not found."""
    subdir = _AGENT_REGISTRY.get(agent_name)
    if subdir:
        candidate = _DEV_AGENTS_DIR / subdir / f"{agent_name}.md"
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")

    # Fallback: glob across all subdirs (handles uvx-installed paths)
    for md_file in _DEV_AGENTS_DIR.rglob(f"{agent_name}.md"):
        return md_file.read_text(encoding="utf-8")

    # Last resort: search relative to this file's installed location
    for candidate in pathlib.Path(__file__).parent.rglob(f"{agent_name}.md"):
        return candidate.read_text(encoding="utf-8")

    available = ", ".join(sorted(_AGENT_REGISTRY.keys()))
    raise FileNotFoundError(
        f"Agent '{agent_name}' not found. Available agents: {available}"
    )


def _load_workflow(workflow_name: str) -> str | None:
    """Load workflow command markdown. Returns None if not found."""
    candidates = [
        _NEXUS_ROOT / ".claude" / "commands" / f"{workflow_name}.md",
        _NEXUS_ROOT / "docs" / "sample-claude-agents" / "commands" / f"{workflow_name}.md",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return None


def _find_claude() -> str | None:
    """Return path to the claude CLI binary, or None if not found."""
    via_which = shutil.which("claude")
    if via_which:
        return via_which
    fallback = pathlib.Path.home() / ".local" / "bin" / "claude"
    if fallback.exists():
        return str(fallback)
    return None


def register_devsecops_tools(mcp: FastMCP) -> None:
    """Register DevSecOps dev-workflow tools onto the MCP server."""

    @mcp.tool()
    async def list_agents() -> str:
        """
        List all available dev-workflow agents organized by category.
        Returns a JSON object with agent categories and names.
        """
        by_category: dict[str, list[str]] = {}
        for agent_name, category in sorted(_AGENT_REGISTRY.items()):
            by_category.setdefault(category, []).append(agent_name)
        for category in by_category:
            by_category[category].sort()

        return json.dumps({
            "agents": by_category,
            "total": len(_AGENT_REGISTRY),
            "categories": sorted(by_category.keys()),
        })

    @mcp.tool()
    async def run_agent(
        agent_name: str,
        context: str,
        workflow: str = "",
        model: str = "claude-sonnet-4-6",
        memory_path: str = "",
        remember: bool = False,
    ) -> str:
        """
        Run a named dev-workflow agent against provided context using the claude CLI.
        Returns findings as JSON.

        Args:
            agent_name: Name of the dev-workflow agent.
                Available: code-reviewer, security, database, deployment, monitoring,
                qa-tester, performance, task-planner, tech-writer, test-planner,
                backend-api, frontend-ui, fullstack-nextjs, react-native,
                software-architect, solution-architect, solution-designer,
                product-manager, savant-fullstack-js, savant-flutter,
                savant-java-spring, savant-react-native
            context: Content to analyze (diff, file content, description, etc.)
            workflow: Optional workflow command name to prepend as instructions
                (e.g. "workflow-review-code", "workflow-review-security")
            model: Claude model to use (default: claude-sonnet-4-6)
            memory_path: Path to .claude/memory/agents/ directory in the target project.
                When provided, past findings are injected as context before the run.
            remember: When True, write findings back to memory after the run.
                Requires memory_path. Writes to personal/ layer (team-safe).
        """
        try:
            system_prompt = _load_dev_agent(agent_name)
        except FileNotFoundError as e:
            return json.dumps({"error": str(e)})

        claude_bin = _find_claude()
        if not claude_bin:
            return json.dumps({
                "error": "claude CLI not found. Install Claude Code or ensure it is on PATH."
            })

        # Build user message — optionally prepend workflow instructions
        user_message = context
        if workflow:
            workflow_text = _load_workflow(workflow)
            if workflow_text:
                user_message = (
                    f"## Workflow: {workflow}\n\n"
                    f"{workflow_text}\n\n"
                    f"---\n\n"
                    f"## Context to analyze:\n\n{context}"
                )

        # Prepend past memory if memory_path is provided
        if memory_path:
            memory_block = build_memory_context_block(memory_path, agent_name)
            if memory_block:
                user_message = memory_block + user_message

        cmd = [
            claude_bin,
            "--print",
            "--dangerously-skip-permissions",
            "--model", model,
            "--system-prompt", system_prompt,
            user_message,
        ]

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=300),
            )

            if result.returncode != 0:
                logger.error("claude CLI error for agent '%s': %s", agent_name, result.stderr)
                return json.dumps({
                    "error": f"claude exited with code {result.returncode}",
                    "detail": result.stderr.strip(),
                })

            findings = result.stdout.strip()

            # Write findings back to memory if requested
            pending_review: list[str] = []
            memory_updated = False
            if memory_path and remember:
                memory_updated, pending_review = update_memory(memory_path, agent_name, findings)

            return json.dumps({
                "agent": agent_name,
                "workflow": workflow or None,
                "findings": findings,
                "model": model,
                "memory_updated": memory_updated,
                "pending_review": pending_review,
            })

        except subprocess.TimeoutExpired:
            return json.dumps({"error": "claude CLI timed out after 300s"})
        except Exception as exc:
            logger.error("run_agent error for '%s': %s", agent_name, exc)
            return json.dumps({"error": str(exc)})

    @mcp.tool()
    async def get_agent_memory(
        agent_name: str,
        memory_path: str,
    ) -> str:
        """
        Read the persistent memory file for a dev-workflow agent.

        Args:
            agent_name: Name of the agent (e.g. code-reviewer, security).
            memory_path: Path to .claude/memory/agents/ in the target project.

        Returns JSON with content and existence flag.
        """
        try:
            from tools.devsecops.memory import read_memory
            content = read_memory(memory_path, agent_name)
            return json.dumps({
                "agent": agent_name,
                "memory_path": memory_path,
                "content": content or "",
                "exists": content is not None,
            })
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    @mcp.tool()
    async def update_agent_memory(
        agent_name: str,
        memory_path: str,
        content: str,
        mode: str = "append",
    ) -> str:
        """
        Update the persistent memory file for a dev-workflow agent.

        Args:
            agent_name: Name of the agent.
            memory_path: Path to .claude/memory/agents/ in the target project.
            content: Findings text to merge into memory.
            mode: "append" (default) | "replace" | "reset"

        Returns JSON confirming the update and any pending review items flagged.
        """
        try:
            ok, pending = update_memory(memory_path, agent_name, content, mode=mode)
            return json.dumps({
                "ok": ok,
                "agent": agent_name,
                "mode": mode,
                "pending_review": pending,
            })
        except Exception as exc:
            return json.dumps({"error": str(exc)})
