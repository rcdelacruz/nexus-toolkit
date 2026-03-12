import json
import logging
import pathlib
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_filetree_tool(mcp: FastMCP) -> None:

    @mcp.tool()
    async def update_file_in_tree(
        path: str,
        content: str,
        nexus_cache: str,
    ) -> str:
        """
        Write a transformed file's content back into the cached file tree.

        Used by API-only clients (e.g. n8n) that cannot write to the filesystem
        directly. After the LLM transforms a queue item, call this tool once per
        file to update 04_file_tree.json with the result.

        The standard Claude Code pipeline does not call this tool — it writes
        files directly using its own file tools.

        Args:
            path: The relative file path (e.g. "components/ui/button.tsx").
                  Must match the `path` field in the queue item.
            content: The fully transformed file content to store.
            nexus_cache: The _nexus_cache value from remap_to_golden_path
                         (e.g. "/tmp/nexus-my-app").

        Returns:
            JSON string: { "ok": true, "path": "..." }
            or           { "error": "..." }
        """
        logger.info(f"update_file_in_tree: {path}")

        try:
            cache_dir = pathlib.Path(nexus_cache)
            file_tree_path = cache_dir / "04_file_tree.json"

            if not file_tree_path.exists():
                return json.dumps({"error": f"04_file_tree.json not found in {nexus_cache}"})

            file_tree = json.loads(file_tree_path.read_text(encoding="utf-8"))
            files: list[dict] = file_tree.get("files", [])

            # Update existing entry or append a new one
            for entry in files:
                if entry.get("path") == path:
                    entry["content"] = content
                    break
            else:
                files.append({"path": path, "content": content})

            file_tree["files"] = files
            file_tree_path.write_text(json.dumps(file_tree), encoding="utf-8")

            logger.info(f"update_file_in_tree complete: {path}")
            return json.dumps({"ok": True, "path": path})

        except Exception as e:
            logger.exception(f"update_file_in_tree failed: {path}")
            return json.dumps({"error": str(e)})
