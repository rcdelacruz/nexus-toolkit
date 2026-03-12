import base64
import io
import json
import logging
import pathlib
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

SUPPORTED_CODE_EXTENSIONS = {".tsx", ".jsx", ".ts", ".js", ".mjs"}
SUPPORTED_STYLE_EXTENSIONS = {".css", ".scss", ".sass", ".less"}
SUPPORTED_ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico"}
PAGE_KEYWORDS = {"page", "screen", "view", "route", "layout", "home", "dashboard", "login", "auth"}

# Discover valid golden paths dynamically from golden_paths/ subdirectories.
_NEXUS_ROOT = pathlib.Path(__file__).parent.parent.parent
_GOLDEN_PATHS_DIR = _NEXUS_ROOT / "golden_paths"
VALID_GOLDEN_PATHS: set[str] = {
    d.name
    for d in _GOLDEN_PATHS_DIR.iterdir()
    if d.is_dir() and (d / "manifest.json").exists()
}


def _classify_file(
    filename: str,
    stem: str,
    suffix: str,
    size_bytes: int,
    content: str,
    components: list,
    pages: list,
    styles: list,
    assets: list,
    unknown: list,
) -> None:
    """Classify a single file into the correct bucket."""
    name_lower = stem.lower()
    file_record = {
        "filename": filename,
        "stem": stem,
        "extension": suffix,
        "size_bytes": size_bytes,
        "content": content,
    }
    if suffix in SUPPORTED_ASSET_EXTENSIONS:
        assets.append({"filename": filename, "extension": suffix, "size_bytes": size_bytes})
    elif suffix in SUPPORTED_STYLE_EXTENSIONS:
        styles.append(file_record)
    elif suffix in SUPPORTED_CODE_EXTENSIONS:
        is_page = any(kw in name_lower for kw in PAGE_KEYWORDS)
        if is_page:
            pages.append(file_record)
        else:
            components.append(file_record)
    else:
        unknown.append({"filename": filename, "extension": suffix})


def register_ingest_tool(mcp: FastMCP) -> None:

    @mcp.tool()
    async def ingest_figma_zip(
        zip_base64: str = "",
        project_dir: str = "",
        golden_path: str = "",
        project_name: str = "my-app",
    ) -> str:
        """
        Ingest a Figma Make export and cache raw files for the pipeline.

        Accepts either a base64-encoded ZIP string OR a path to an already-unzipped
        local directory — whichever is more convenient for the user.

        Args:
            zip_base64: Base64-encoded ZIP file (the Figma Make export). Mutually
                        exclusive with project_dir; provide one or the other.
            project_dir: Absolute path to an unzipped Figma Make export directory on
                         the local filesystem (e.g. "/Users/me/Downloads/figma-export").
                         Use this instead of zip_base64 to avoid the base64 step.
            golden_path: Required. Target stack — ask the user which they want:
                         'nextjs-fullstack' | 'nextjs-static' | 't3-stack' | 'vite-spa' | 'monorepo'
            project_name: Slug used for the root folder and package.json name.

        Returns:
            JSON with the manifest summary and _nexus_cache path.
        """
        logger.info(f"ingest_figma_zip called - golden_path: '{golden_path}', project: {project_name}")

        if not golden_path.strip():
            return json.dumps({
                "error": (
                    "golden_path is required. Ask the user which stack they want, then re-run.\n"
                    f"Available: {', '.join(sorted(VALID_GOLDEN_PATHS))}\n"
                    "  nextjs-fullstack — Next.js + tRPC + Prisma + NextAuth + Zustand\n"
                    "  nextjs-static    — Next.js static export (landing pages, no backend)\n"
                    "  t3-stack         — T3 (Next.js + tRPC + Prisma + NextAuth), all under src/\n"
                    "  vite-spa         — Vite + React + React Router v7\n"
                    "  monorepo         — Turborepo with apps/web + apps/marketing + packages/ui"
                )
            })

        if golden_path not in VALID_GOLDEN_PATHS:
            return json.dumps({"error": f"Invalid golden_path '{golden_path}'. Must be one of: {', '.join(sorted(VALID_GOLDEN_PATHS))}"})

        if not zip_base64.strip() and not project_dir.strip():
            return json.dumps({"error": "Provide either zip_base64 (base64 ZIP string) or project_dir (path to unzipped folder)."})

        components: list = []
        pages: list = []
        styles: list = []
        assets: list = []
        unknown: list = []
        total_files = 0

        try:
            # ── Path A: read from a local directory ──────────────────────────
            if project_dir.strip():
                root = Path(project_dir.strip()).expanduser().resolve()
                if not root.exists():
                    return json.dumps({"error": f"project_dir does not exist: {root}"})
                if not root.is_dir():
                    return json.dumps({"error": f"project_dir is not a directory: {root}"})

                for file_path in sorted(root.rglob("*")):
                    if not file_path.is_file():
                        continue
                    parts = file_path.relative_to(root).parts
                    if any(p.startswith(".") or p in {"node_modules", ".next"} for p in parts):
                        continue

                    total_files += 1
                    suffix = file_path.suffix.lower()
                    rel = file_path.relative_to(root).as_posix()

                    if suffix in SUPPORTED_ASSET_EXTENSIONS:
                        assets.append({"filename": rel, "extension": suffix, "size_bytes": file_path.stat().st_size})
                        continue

                    try:
                        content = file_path.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        logger.debug("Skipping undecodable binary file: %s", rel)
                        assets.append({"filename": rel, "extension": suffix, "size_bytes": file_path.stat().st_size})
                        continue
                    except Exception:
                        content = ""

                    _classify_file(rel, file_path.stem, suffix, file_path.stat().st_size, content,
                                   components, pages, styles, assets, unknown)

            # ── Path B: read from a base64 ZIP ───────────────────────────────
            else:
                try:
                    zip_bytes = base64.b64decode(zip_base64)
                except Exception:
                    return json.dumps({"error": "zip_base64 is not valid base64"})

                zip_buffer = io.BytesIO(zip_bytes)
                if not zipfile.is_zipfile(zip_buffer):
                    return json.dumps({"error": "Provided data is not a valid ZIP file"})
                zip_buffer.seek(0)

                with zipfile.ZipFile(zip_buffer, "r") as zf:
                    for entry in zf.infolist():
                        if entry.is_dir():
                            continue

                        parts = PurePosixPath(entry.filename).parts
                        if any(p.startswith(".") or p in {"node_modules", ".next"} for p in parts):
                            continue

                        total_files += 1
                        path = PurePosixPath(entry.filename)
                        suffix = path.suffix.lower()

                        try:
                            raw = zf.read(entry.filename)
                            content = raw.decode("utf-8")
                        except UnicodeDecodeError:
                            logger.debug("Skipping undecodable binary file: %s", entry.filename)
                            assets.append({"filename": entry.filename, "extension": suffix, "size_bytes": entry.file_size})
                            continue
                        except Exception:
                            content = ""

                        _classify_file(entry.filename, path.stem, suffix, entry.file_size, content,
                                       components, pages, styles, assets, unknown)

            manifest = {
                "project_name": project_name,
                "golden_path": golden_path,
                "total_files": total_files,
                "summary": {
                    "components": len(components),
                    "pages": len(pages),
                    "styles": len(styles),
                    "assets": len(assets),
                    "unknown": len(unknown),
                },
                "components": components,
                "pages": pages,
                "styles": styles,
                "assets": assets,
                "unknown": unknown,
            }

            # Write full manifest to disk cache — wipe any stale run first
            cache_dir = pathlib.Path(f"/tmp/nexus-{project_name}")
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True)
            (cache_dir / "01_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            logger.info(
                f"ingest_figma_zip complete - {total_files} files: "
                f"{len(components)} components, {len(pages)} pages, "
                f"{len(styles)} styles, {len(assets)} assets | "
                f"golden_path: {golden_path}"
            )

            return json.dumps({
                "project_name": project_name,
                "golden_path": golden_path,
                "total_files": total_files,
                "summary": {
                    "components": len(components),
                    "pages": len(pages),
                    "styles": len(styles),
                    "assets": len(assets),
                    "unknown": len(unknown),
                },
                "_nexus_cache": str(cache_dir),
            })

        except zipfile.BadZipFile:
            return json.dumps({"error": "Corrupted or invalid ZIP file"})
        except Exception as e:
            logger.exception("Unexpected error in ingest_figma_zip")
            return json.dumps({"error": f"Unexpected error: {str(e)}"})
