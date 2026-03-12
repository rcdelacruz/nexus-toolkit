import io
import json
import logging
import pathlib
import zipfile
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def _load_input(json_str: str, cache_file: str) -> dict:
    """Load the full input data, preferring the disk cache when available."""
    data = json.loads(json_str)
    cache = data.get("_nexus_cache")
    if cache:
        full = pathlib.Path(cache, cache_file).read_text(encoding="utf-8")
        return json.loads(full)
    return data


def register_package_tool(mcp: FastMCP) -> None:

    @mcp.tool()
    async def package_output(file_tree_json: str) -> str:
        """
        Package the generated file tree into a base64-encoded ZIP file.

        Takes the output of remap_to_golden_path and materializes it into a
        downloadable ZIP that can be sent to a frontend, stored, or extracted
        directly to disk.

        Args:
            file_tree_json: JSON string returned by remap_to_golden_path,
                            containing { "project_name": ..., "files": [...] }.

        Returns:
            JSON string with:
            {
              "project_name": "my-app",
              "golden_path": "nextjs-fullstack",
              "total_files": 42,
              "zip_data": "<base64-encoded ZIP>",
              "size_bytes": 12345
            }
        """
        logger.info("package_output called")

        try:
            file_tree = _load_input(file_tree_json, "04_file_tree.json")
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid file tree JSON: {str(e)}"})
        except Exception as e:
            return json.dumps({"error": f"Failed to load file tree: {str(e)}"})

        if "error" in file_tree:
            return json.dumps({"error": f"File tree contains error: {file_tree['error']}"})

        files = file_tree.get("files", [])
        if not files:
            return json.dumps({"error": "No files to package — file tree is empty"})

        project_name = file_tree.get("project_name", "my-app")
        golden_path = file_tree.get("golden_path", "nextjs-fullstack")
        passthrough_paths: set[str] = set(file_tree.get("passthrough_paths", []))

        # ── Strip orphan files before packaging ───────────────────────────────
        # Keep a file if ANY of:
        #   1. It is reachable (imported directly or transitively from an entry point)
        #   2. It is a config/tooling file (Dockerfile, package.json, .prettierrc, etc.)
        #   3. It is a shadcn/ui passthrough primitive (explicit component library)
        #   4. It is listed in the golden path manifest's requiredFiles
        # Reference boilerplate stubs that the Figma design never imports are
        # silently dropped — they add noise and dead code to the output ZIP.
        from tools.figma.validate import _build_reachability, _is_config_file
        from tools.figma.remap import BINARY_PLACEHOLDER

        # Load requiredFiles from the golden path manifest so they are never stripped
        NEXUS_ROOT = pathlib.Path(__file__).parent.parent.parent
        gp_manifest_path = NEXUS_ROOT / "golden_paths" / golden_path / "manifest.json"
        required_files: set[str] = set()
        if gp_manifest_path.exists():
            try:
                gp_manifest = json.loads(gp_manifest_path.read_text(encoding="utf-8"))
                required_files = set(gp_manifest.get("requiredFiles", []))
            except Exception:
                pass

        reachable = _build_reachability(files)
        kept_files: list[dict] = []
        stripped_paths: list[str] = []

        for file_entry in files:
            path: str = file_entry.get("path", "unknown.txt")
            content: str = file_entry.get("content", "")

            # Always skip binary asset placeholders
            if content == BINARY_PLACEHOLDER:
                stripped_paths.append(path)
                continue

            if path in reachable or _is_config_file(path) or path in passthrough_paths or path in required_files:
                kept_files.append(file_entry)
            else:
                stripped_paths.append(path)
                logger.info(f"Stripping orphan file from ZIP: {path}")

        if stripped_paths:
            logger.info(f"Stripped {len(stripped_paths)} orphan/unused files from output ZIP")

        # Determine cache dir and output ZIP path
        cache_dir = pathlib.Path(f"/tmp/nexus-{project_name}")
        cache_dir.mkdir(parents=True, exist_ok=True)
        zip_path = cache_dir / f"{project_name}.zip"

        # Build the ZIP in memory, then write to disk
        zip_buffer = io.BytesIO()

        try:
            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for file_entry in kept_files:
                    path = file_entry.get("path", "unknown.txt")
                    content = file_entry.get("content", "")
                    archive_path = f"{project_name}/{path}"
                    zf.writestr(archive_path, content)

        except Exception as e:
            logger.exception("Error building ZIP")
            return json.dumps({"error": f"Failed to build ZIP: {str(e)}"})

        zip_bytes = zip_buffer.getvalue()
        zip_path.write_bytes(zip_bytes)
        size_bytes = len(zip_bytes)

        logger.info(
            f"package_output complete - {len(kept_files)} files, "
            f"{size_bytes} bytes, project: {project_name}, path: {zip_path}"
        )

        return json.dumps({
            "project_name": project_name,
            "golden_path": golden_path,
            "total_files": len(kept_files),
            "stripped_files": stripped_paths,
            "size_bytes": size_bytes,
            "zip_path": str(zip_path),
            "files": kept_files,
            "instructions": (
                f"ZIP is ready at {zip_path}. "
                f"Run: cp {zip_path} ~/Desktop/ && "
                f"unzip ~/Desktop/{project_name}.zip && "
                f"cd {project_name} && pnpm install && pnpm dev"
            ),
        })
