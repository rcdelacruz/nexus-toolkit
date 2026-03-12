import logging
import os
import sys
from mcp.server.fastmcp import FastMCP
from tools.search import register_search_tools
from tools.figma import register_figma_tools
from tools.devsecops import register_devsecops_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Read host/port at module level so FastMCP is initialized with the correct
# values before main() is called. MCP_HOST / MCP_PORT take precedence over
# the legacy FASTMCP_* vars so that "MCP_HOST=0.0.0.0 MCP_PORT=3900 nexus-mcp"
# works as documented without any ordering surprises.
_host = os.environ.get("MCP_HOST") or os.environ.get("FASTMCP_HOST", "127.0.0.1")
_port = int(os.environ.get("MCP_PORT") or os.environ.get("FASTMCP_PORT", "8000"))

mcp = FastMCP(
    "Nexus-MCP",
    host=_host,
    port=_port,
    # stateless_http=True: no session handshake required — each POST is
    # independent. Needed for n8n SSH nodes that call tools via raw curl.
    stateless_http=True,
    # json_response=True: always return plain JSON (no SSE wrapping).
    # Without this the server requires Accept: application/json, text/event-stream
    # and wraps responses in SSE format, breaking json.loads() in curl scripts.
    json_response=True,
)
register_search_tools(mcp)
register_figma_tools(mcp)
register_devsecops_tools(mcp)
logger.info("Nexus MCP server initialized")


def main() -> None:
    """Entry point for the MCP server.

    Transport selection:
      MCP_TRANSPORT env var: stdio | sse | http  (default: stdio)
      --transport=sse flag also works

    SSE/HTTP env vars:
      MCP_HOST (default: 0.0.0.0)
      MCP_PORT (default: 3001)
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--transport" and i + 1 < len(sys.argv):
            transport = sys.argv[i + 1].lower()
        elif arg.startswith("--transport="):
            transport = arg.split("=", 1)[1].lower()

    if transport == "stdio":
        logger.info("Starting Nexus MCP -- transport: stdio")
        mcp.run(transport="stdio")
    elif transport in ("sse", "http", "streamable-http"):
        actual_transport = "streamable-http" if transport in ("streamable-http", "http") else "sse"
        logger.info(f"Starting Nexus MCP -- transport: {actual_transport} {_host}:{_port}")
        mcp.run(transport=actual_transport)
    else:
        logger.error(f"Unknown transport: {transport}")
        sys.exit(1)


if __name__ == "__main__":
    main()
