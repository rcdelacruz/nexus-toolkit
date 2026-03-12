from tools.devsecops.agent_runner import register_devsecops_tools
from mcp.server.fastmcp import FastMCP


def register_devsecops_tools_all(mcp: FastMCP) -> None:
    """Register DevSecOps dev-workflow tools onto the MCP server."""
    register_devsecops_tools(mcp)


__all__ = ["register_devsecops_tools_all", "register_devsecops_tools"]
