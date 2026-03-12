"""
ingest_from_codebase — migrate an existing project to a Nexus golden path.

Covers Scenario C: the user already has a working project (React, Next.js, Vite,
or any stack) and wants to enforce golden path conventions on it without starting
from scratch.

Key differences from ingest_figma_zip:
  - Source is real production code, not Figma-generated stubs.
  - _is_infra_content() filtering is skipped in remap_to_golden_path — existing
    components legitimately import Prisma, tRPC, etc.
  - Queue file framing tells the LLM agent to "migrate conventions" rather than
    "convert Figma source" or "create from scratch".
  - Config/tooling files (package.json, tsconfig, etc.) are skipped so the
    golden path boilerplate versions take precedence.
  - A broader set of build output and generated directories are excluded.

The manifest produced is identical in shape to ingest_figma_zip output, so
remap_to_golden_path, validate_output, and package_output are unchanged.
"""

import json
import logging
import pathlib
import shutil

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

_NEXUS_ROOT = pathlib.Path(__file__).parent.parent.parent
_GOLDEN_PATHS_DIR = _NEXUS_ROOT / "golden_paths"

VALID_GOLDEN_PATHS: set[str] = {
    d.name
    for d in _GOLDEN_PATHS_DIR.iterdir()
    if d.is_dir() and (d / "manifest.json").exists()
}

# Directories to skip entirely when reading an existing project
_SKIP_DIRS: set[str] = {
    "node_modules", ".next", ".nuxt", "dist", "build", "out",
    ".git", ".svn", ".turbo", ".vercel", "coverage", ".nyc_output",
    "generated", ".generated", "__pycache__", ".venv", "venv",
}

# File extensions treated as source code
_CODE_EXTENSIONS: set[str] = {".tsx", ".jsx", ".ts", ".js", ".mjs"}

# File extensions treated as stylesheets
_STYLE_EXTENSIONS: set[str] = {".css", ".scss", ".sass", ".less"}

# File extensions treated as binary assets
_ASSET_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico"}

# Page-keyword detection (same as ingest.py)
_PAGE_KEYWORDS: set[str] = {
    "page", "screen", "view", "route", "layout",
    "home", "dashboard", "login", "auth",
}

# Stems that are config/tooling files — the golden path boilerplate provides
# these, so we skip the existing versions to avoid overwriting them.
_CONFIG_STEMS: set[str] = {
    "package", "tsconfig", "jsconfig",
    "next.config", "vite.config", "astro.config",
    "tailwind.config", "postcss.config",
    "eslint.config", ".eslintrc", "prettier.config", ".prettierrc",
    "jest.config", "vitest.config", "playwright.config",
    "drizzle.config", "prisma.config",
    "dockerfile", "docker-compose",
    "readme", "license", "changelog",
    ".env", ".env.example", ".env.local",
    ".gitignore", ".gitattributes",
}


def _is_config_file(stem: str, suffix: str) -> bool:
    """Return True for files the golden path boilerplate should own."""
    lower_stem = stem.lower()
    lower_full = (stem + suffix).lower()
    return (
        lower_stem in _CONFIG_STEMS
        or lower_full in _CONFIG_STEMS
        or suffix.lower() in {".json", ".lock", ".toml", ".yaml", ".yml", ".md"}
    )


def _classify_source_file(
    rel: str,
    stem: str,
    suffix: str,
    size_bytes: int,
    content: str,
    components: list,
    pages: list,
    styles: list,
    assets: list,
) -> None:
    """Bucket an existing source file the same way ingest_figma_zip does."""
    record = {
        "filename": rel,
        "stem": stem,
        "extension": suffix,
        "size_bytes": size_bytes,
        "content": content,
    }
    if suffix in _STYLE_EXTENSIONS:
        styles.append(record)
    elif suffix in _CODE_EXTENSIONS:
        is_page = any(kw in stem.lower() for kw in _PAGE_KEYWORDS)
        if is_page:
            pages.append(record)
        else:
            components.append(record)


def register_codebase_ingest_tool(mcp: FastMCP) -> None:

    @mcp.tool()
    async def ingest_from_codebase(
        project_dir: str,
        golden_path: str,
        project_name: str = "",
    ) -> str:
        """
        Migrate an existing project to a Nexus golden path.

        Reads the source files from an existing project directory and produces
        a manifest that feeds into remap_to_golden_path. The LLM agent then
        rewrites each component to conform to the target golden path's conventions
        while preserving the original UI and functionality.

        Config and tooling files (package.json, tsconfig.json, etc.) are excluded
        from the migration queue — the golden path's boilerplate versions replace
        them automatically.

        Args:
            project_dir: Absolute path to the existing project root.
                         E.g. "/Users/me/projects/my-old-react-app".
            golden_path: Target stack to migrate toward.
                         E.g. "nextjs-fullstack", "vite-spa".
            project_name: Output project slug. Defaults to the source directory name.

        Returns:
            JSON manifest (same shape as ingest_figma_zip) with source_type: "codebase".
            Pass this directly to remap_to_golden_path.
        """
        logger.info(
            f"ingest_from_codebase called — project_dir: '{project_dir}', "
            f"golden_path: '{golden_path}'"
        )

        # ── Validate inputs ───────────────────────────────────────────────────
        if not project_dir.strip():
            return json.dumps({"error": "project_dir is required."})

        root = pathlib.Path(project_dir.strip()).expanduser().resolve()
        if not root.exists():
            return json.dumps({"error": f"project_dir does not exist: {root}"})
        if not root.is_dir():
            return json.dumps({"error": f"project_dir is not a directory: {root}"})

        if not golden_path.strip():
            return json.dumps({
                "error": (
                    "golden_path is required. Available: "
                    f"{', '.join(sorted(VALID_GOLDEN_PATHS))}"
                )
            })

        if golden_path not in VALID_GOLDEN_PATHS:
            return json.dumps({
                "error": (
                    f"Invalid golden_path '{golden_path}'. "
                    f"Must be one of: {', '.join(sorted(VALID_GOLDEN_PATHS))}"
                )
            })

        resolved_project_name = project_name.strip() or root.name

        # ── Walk the source directory ─────────────────────────────────────────
        components: list = []
        pages: list = []
        styles: list = []
        assets: list = []
        skipped_config: int = 0
        total_files: int = 0

        for file_path in sorted(root.rglob("*")):
            if not file_path.is_file():
                continue

            parts = file_path.relative_to(root).parts

            # Skip hidden dirs, build output, generated dirs, node_modules, etc.
            if any(p in _SKIP_DIRS or p.startswith(".") for p in parts):
                continue

            total_files += 1
            suffix = file_path.suffix.lower()
            rel = file_path.relative_to(root).as_posix()

            # Assets — copy as-is
            if suffix in _ASSET_EXTENSIONS:
                assets.append({
                    "filename": rel,
                    "extension": suffix,
                    "size_bytes": file_path.stat().st_size,
                })
                continue

            # Config / tooling — skip, let boilerplate own these
            if _is_config_file(file_path.stem, suffix):
                skipped_config += 1
                logger.debug(f"Skipping config file: {rel}")
                continue

            # Read text content
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                logger.debug(f"Skipping undecodable binary: {rel}")
                assets.append({
                    "filename": rel,
                    "extension": suffix,
                    "size_bytes": file_path.stat().st_size,
                })
                continue
            except Exception:
                content = ""

            _classify_source_file(
                rel, file_path.stem, suffix,
                file_path.stat().st_size, content,
                components, pages, styles, assets,
            )

        logger.info(
            f"ingest_from_codebase scan complete — "
            f"{len(components)} components, {len(pages)} pages, "
            f"{len(styles)} styles, {len(assets)} assets, "
            f"{skipped_config} config files skipped"
        )

        if not components and not pages and not styles:
            return json.dumps({
                "error": (
                    f"No migratable source files found in '{root}'. "
                    f"Ensure the directory contains .tsx/.ts/.jsx/.js/.css files "
                    f"and is not just config/tooling files."
                )
            })

        # ── Build manifest ────────────────────────────────────────────────────
        manifest = {
            "project_name": resolved_project_name,
            "golden_path": golden_path,
            "source_type": "codebase",
            "source_dir": str(root),
            "total_files": total_files,
            "summary": {
                "components": len(components),
                "pages": len(pages),
                "styles": len(styles),
                "assets": len(assets),
                "skipped_config": skipped_config,
            },
            "components": components,
            "pages": pages,
            "styles": styles,
            "assets": assets,
            "unknown": [],
        }

        # ── Write to disk cache ───────────────────────────────────────────────
        cache_dir = pathlib.Path(f"/tmp/nexus-{resolved_project_name}")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True)
        (cache_dir / "01_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        return json.dumps({
            "project_name": resolved_project_name,
            "golden_path": golden_path,
            "source_type": "codebase",
            "source_dir": str(root),
            "total_files": total_files,
            "summary": manifest["summary"],
            "_nexus_cache": str(cache_dir),
        })
