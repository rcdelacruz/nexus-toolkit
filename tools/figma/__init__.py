from tools.figma.ingest import register_ingest_tool
from tools.figma.prompt_ingest import register_prompt_ingest_tool
from tools.figma.codebase_ingest import register_codebase_ingest_tool
from tools.figma.remap import register_remap_tool
from tools.figma.validate import register_validate_tool
from tools.figma.package import register_package_tool
from tools.figma.filetree import register_filetree_tool
from mcp.server.fastmcp import FastMCP


def register_figma_tools(mcp: FastMCP) -> None:
    """Register Figma pipeline tools onto the MCP server."""
    register_ingest_tool(mcp)
    register_prompt_ingest_tool(mcp)
    register_codebase_ingest_tool(mcp)
    register_remap_tool(mcp)
    register_validate_tool(mcp)
    register_package_tool(mcp)
    register_filetree_tool(mcp)


__all__ = ["register_figma_tools"]
