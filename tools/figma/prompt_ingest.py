"""
ingest_from_prompt — text-description-driven ingestion for the Nexus pipeline.

Covers two scenarios that ingest_figma_zip cannot:
  A. Scaffold only — "give me a clean nextjs-fullstack starter" (no design yet)
  B. Description-driven — "build a SaaS landing page with hero, pricing, testimonials"

Produces the same manifest format as ingest_figma_zip so the rest of the pipeline
(remap_to_golden_path → agent → validate_output → package_output) is unchanged.
The only difference downstream is source_type: "prompt" in the manifest, which
causes remap_to_golden_path to frame queue files as "design from scratch" rather
than "convert Figma source".

NOTE: This tool expects pages and components to be provided explicitly.
Callers are responsible for decomposing the description into pages/components:
  - Claude Code (MCP): passes them directly based on its own understanding
  - n8n: uses a dedicated "Decompose Description" LLM step before calling this tool
  - CLI: uses _decompose_description() in nexus_cli.py before calling this tool
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


# ── Spec builder ──────────────────────────────────────────────────────────────

def _build_spec(stem: str, project_name: str, description: str, golden_path: str) -> str:
    """
    Build a concise design specification string for a single component.
    This becomes `figma_source` in the queue file — the LLM reads it as the
    design brief and creates the component from scratch.
    """
    return (
        f"## Project: {project_name}\n\n"
        f"{description.strip()}\n\n"
        f"## Component: {stem}\n\n"
        f"Design tokens, typography, and colours must be consistent with a modern "
        f"{golden_path} application and with any other components in the same project.\n"
        f"Follow all `.claude/agents/{golden_path}.md` rules.\n"
        f"There is no Figma source — create this component entirely from the spec above."
    )


def _make_entry(stem: str, project_name: str, description: str, golden_path: str) -> dict:
    """Build a manifest component/page entry for a prompt-derived component."""
    spec = _build_spec(stem, project_name, description, golden_path)
    return {
        "filename": f"{stem}.tsx",
        "stem": stem,
        "extension": ".tsx",
        "size_bytes": len(spec.encode()),
        "content": spec,
    }


# ── Tool registration ─────────────────────────────────────────────────────────

def register_prompt_ingest_tool(mcp: FastMCP) -> None:

    @mcp.tool()
    async def ingest_from_prompt(
        description: str,
        golden_path: str,
        project_name: str = "my-app",
        pages: list[str] | None = None,
        components: list[str] | None = None,
    ) -> str:
        """
        Generate a Nexus pipeline manifest from a text description — no Figma file needed.

        Covers two use cases:
          • Scaffold only: pass a short description like "scaffold a nextjs-fullstack starter"
            and leave pages/components empty — you get the golden path boilerplate with no UI.
          • Description-driven: describe what to build and pass explicit pages and components.
            The pipeline creates each one from scratch guided by the description.

        IMPORTANT: pages and components should be determined by the caller before invoking
        this tool. Do not rely on automatic inference — pass them explicitly.

        The manifest produced is identical in format to ingest_figma_zip output, so
        remap_to_golden_path, validate_output, and package_output work unchanged.

        Args:
            description: Natural language description of what to build.
                         E.g. "A SaaS landing page with a hero, features grid, pricing
                         table, testimonials, and a footer. Modern, clean aesthetic."
            golden_path: Target stack. One of the available golden paths.
            project_name: Slug used for the output folder and package.json name.
            pages: List of page component names to create.
                   E.g. ["HomePage", "AboutPage", "PricingPage"].
            components: List of section/UI component names to create.
                        E.g. ["HeroSection", "FeaturesSection", "PricingSection", "Footer"].

        Returns:
            JSON manifest (same shape as ingest_figma_zip) with source_type: "prompt".
            Pass this directly to remap_to_golden_path.
        """
        logger.info(
            f"ingest_from_prompt called — golden_path: '{golden_path}', "
            f"project: '{project_name}', "
            f"pages: {pages}, components: {components}"
        )

        # ── Validate inputs ───────────────────────────────────────────────────
        if not description.strip():
            return json.dumps({"error": "description is required."})

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

        resolved_pages = list(pages) if pages else []
        resolved_components = list(components) if components else []

        logger.info(
            f"Resolved — pages: {resolved_pages}, components: {resolved_components}"
        )

        # ── Build manifest entries ────────────────────────────────────────────
        page_entries = [
            _make_entry(stem, project_name, description, golden_path)
            for stem in resolved_pages
        ]
        component_entries = [
            _make_entry(stem, project_name, description, golden_path)
            for stem in resolved_components
        ]

        total = len(page_entries) + len(component_entries)

        manifest = {
            "project_name": project_name,
            "golden_path": golden_path,
            "source_type": "prompt",
            "description": description.strip(),
            "total_files": total,
            "summary": {
                "components": len(component_entries),
                "pages": len(page_entries),
                "styles": 0,
                "assets": 0,
                "unknown": 0,
            },
            "components": component_entries,
            "pages": page_entries,
            "styles": [],
            "assets": [],
            "unknown": [],
        }

        # ── Write to disk cache ───────────────────────────────────────────────
        cache_dir = pathlib.Path(f"/tmp/nexus-{project_name}")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True)
        (cache_dir / "01_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        logger.info(
            f"ingest_from_prompt complete — {total} virtual components "
            f"({len(page_entries)} pages, {len(component_entries)} sections/ui)"
        )

        return json.dumps({
            "project_name": project_name,
            "golden_path": golden_path,
            "source_type": "prompt",
            "total_files": total,
            "summary": manifest["summary"],
            "_nexus_cache": str(cache_dir),
        })
