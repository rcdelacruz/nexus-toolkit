"""Tests for tools/devsecops/agent_runner.py"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from tools.devsecops.agent_runner import _load_dev_agent, register_devsecops_tools


# ── helpers ───────────────────────────────────────────────────────────────────


def _extract_tool(tool_name: str):
    """Pull a named async tool function out of register_devsecops_tools."""
    captured = {}
    mock_mcp = MagicMock()

    def _tool_decorator(fn):
        captured[fn.__name__] = fn
        return fn

    mock_mcp.tool.return_value = _tool_decorator
    register_devsecops_tools(mock_mcp)
    return captured[tool_name]


# ══════════════════════════════════════════════════════════════════════════════
# _load_dev_agent
# ══════════════════════════════════════════════════════════════════════════════


class TestLoadDevAgent:

    def test_returns_content_for_known_agent(self):
        content = _load_dev_agent("code-reviewer")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_known_agent_content_is_non_empty_string(self):
        content = _load_dev_agent("security")
        assert content.strip() != ""

    def test_returns_empty_string_for_unknown_agent(self):
        """Unknown agent name should raise FileNotFoundError, not return empty string."""
        with pytest.raises(FileNotFoundError) as exc_info:
            _load_dev_agent("nonexistent-agent-xyz")
        assert "nonexistent-agent-xyz" in str(exc_info.value)

    def test_error_message_lists_available_agents(self):
        with pytest.raises(FileNotFoundError) as exc_info:
            _load_dev_agent("does-not-exist")
        assert "code-reviewer" in str(exc_info.value)

    def test_all_registered_agents_loadable(self):
        """Every agent in the registry must resolve to a real file."""
        from tools.devsecops.agent_runner import _AGENT_REGISTRY
        for agent_name in _AGENT_REGISTRY:
            content = _load_dev_agent(agent_name)
            assert len(content) > 0, f"Empty content for agent: {agent_name}"


# ══════════════════════════════════════════════════════════════════════════════
# run_agent — Claude Code mode (CLAUDECODE env var)
# ══════════════════════════════════════════════════════════════════════════════


class TestRunAgentClaudeCodeMode:

    @pytest.mark.asyncio
    async def test_claudecode_mode_returns_system_prompt(self):
        """When CLAUDECODE=1 is set, run_agent returns system_prompt without subprocess."""
        run_agent = _extract_tool("run_agent")
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            raw = await run_agent(agent_name="code-reviewer", context="Review this code: x = 1")
        result = json.loads(raw)
        assert "error" not in result
        assert "system_prompt" in result
        assert len(result["system_prompt"]) > 0

    @pytest.mark.asyncio
    async def test_claudecode_mode_returns_user_message(self):
        """The context is returned as user_message in Claude Code mode."""
        run_agent = _extract_tool("run_agent")
        context_text = "Check security of this snippet: password = '123'"
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            raw = await run_agent(agent_name="security", context=context_text)
        result = json.loads(raw)
        assert "user_message" in result
        assert context_text in result["user_message"]

    @pytest.mark.asyncio
    async def test_claudecode_mode_returns_agent_name(self):
        run_agent = _extract_tool("run_agent")
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            raw = await run_agent(agent_name="code-reviewer", context="some code")
        result = json.loads(raw)
        assert result["agent"] == "code-reviewer"

    @pytest.mark.asyncio
    async def test_claudecode_mode_no_subprocess(self):
        """In Claude Code mode, no subprocess should be spawned."""
        run_agent = _extract_tool("run_agent")
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                await run_agent(agent_name="code-reviewer", context="code here")
                mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_claudecode_env_var_controls_branch(self):
        """Without CLAUDECODE set, the subprocess branch is attempted (not the prompt-return branch)."""
        run_agent = _extract_tool("run_agent")
        env_without_claudecode = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        with patch.dict(os.environ, env_without_claudecode, clear=True):
            # Patch _find_claude to avoid needing a real binary installed
            with patch("tools.devsecops.agent_runner._find_claude", return_value=None):
                raw = await run_agent(agent_name="code-reviewer", context="some code")
        result = json.loads(raw)
        # Without CLAUDECODE, it falls through to subprocess path.
        # If claude is not found, it should return an error about the CLI.
        assert "error" in result
        assert "claude" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_claudecode_mode_unknown_agent_returns_error(self):
        """Unknown agent name should return an error JSON, not raise."""
        run_agent = _extract_tool("run_agent")
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            raw = await run_agent(agent_name="nonexistent-agent-xyz", context="code")
        result = json.loads(raw)
        assert "error" in result
        assert "nonexistent-agent-xyz" in result["error"]

    @pytest.mark.asyncio
    async def test_claudecode_mode_remember_adds_after_response(self):
        """When remember=True, after_response instructions are included."""
        run_agent = _extract_tool("run_agent")
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            raw = await run_agent(
                agent_name="code-reviewer",
                context="some code",
                memory_path="/tmp/test-memory-agents",
                remember=True,
            )
        result = json.loads(raw)
        assert "after_response" in result
        assert len(result["after_response"]) > 0
