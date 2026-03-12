"""Tests for the Figma pipeline tools (ingest → remap → validate → package)."""
import base64
import io
import json
import pathlib
import zipfile
from unittest.mock import MagicMock

import pytest

from tools.figma.ingest import register_ingest_tool
from tools.figma.remap import register_remap_tool
from tools.figma.package import register_package_tool


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_tool(register_fn):
    """
    Pull the inner async function out of a register_* closure without a real
    FastMCP server running.  Works because @mcp.tool() returns the function
    unchanged, so we just capture whatever gets decorated.
    """
    captured = {}
    mock_mcp = MagicMock()
    mock_mcp.tool.return_value = lambda f: captured.setdefault("fn", f) or f
    register_fn(mock_mcp)
    return captured["fn"]


def _make_zip(files: dict[str, str]) -> str:
    """Build an in-memory ZIP and return it as a base64 string."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return base64.b64encode(buf.getvalue()).decode()


# ── shared fixtures ────────────────────────────────────────────────────────────

SAMPLE_FILES = {
    "components/Button.tsx": (
        "import React from 'react';\n"
        "export default function Button({ children }) {\n"
        "  return <button style={{backgroundColor:'#3B82F6',color:'#FFFFFF',"
        "fontFamily:'Inter'}}>{children}</button>;\n"
        "}"
    ),
    "components/Card.tsx": (
        "import React from 'react';\n"
        "export const Card = ({ title }) => (\n"
        "  <div style={{backgroundColor:'#FFFFFF',border:'1px solid #E5E7EB'}}>\n"
        "    <h3>{title}</h3>\n"
        "  </div>\n"
        ");\n"
    ),
    "pages/home.tsx": (
        "import React from 'react';\n"
        "import Button from '../components/Button';\n"
        "export default function HomePage() {\n"
        "  return <div><Button>Go</Button></div>;\n"
        "}"
    ),
    "styles/globals.css": (
        ":root { --color-primary: #3B82F6; }\n"
        "body { font-family: 'Inter', sans-serif; font-size: 16px; }\n"
    ),
}

SAMPLE_ZIP_B64 = _make_zip(SAMPLE_FILES)


# ── pipeline helpers ───────────────────────────────────────────────────────────

async def _make_manifest(golden_path="nextjs-fullstack", project_name="my-app") -> str:
    ingest = _extract_tool(register_ingest_tool)
    return await ingest(SAMPLE_ZIP_B64, golden_path=golden_path, project_name=project_name)


async def _make_file_tree(golden_path="nextjs-fullstack", project_name="my-app") -> str:
    remap = _extract_tool(register_remap_tool)
    return await remap(await _make_manifest(golden_path=golden_path, project_name=project_name))


# ══════════════════════════════════════════════════════════════════════════════
# 1. ingest_figma_zip
# ══════════════════════════════════════════════════════════════════════════════

class TestIngestFigmaZip:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.tool = _extract_tool(register_ingest_tool)

    @pytest.mark.asyncio
    async def test_valid_zip_returns_manifest(self):
        result = json.loads(await self.tool(SAMPLE_ZIP_B64, golden_path="nextjs-fullstack"))
        assert "error" not in result
        assert result["project_name"] == "my-app"
        assert result["golden_path"] == "nextjs-fullstack"
        assert result["total_files"] == 4

    @pytest.mark.asyncio
    async def test_classifies_components_and_pages(self):
        result = json.loads(await self.tool(SAMPLE_ZIP_B64, golden_path="nextjs-fullstack"))
        assert result["summary"]["components"] == 2
        assert result["summary"]["pages"] == 1
        assert result["summary"]["styles"] == 1

    @pytest.mark.asyncio
    async def test_custom_project_name_and_golden_path(self):
        result = json.loads(await self.tool(SAMPLE_ZIP_B64, golden_path="t3-stack", project_name="acme"))
        assert result["project_name"] == "acme"
        assert result["golden_path"] == "t3-stack"

    @pytest.mark.asyncio
    async def test_invalid_golden_path(self):
        result = json.loads(await self.tool(SAMPLE_ZIP_B64, golden_path="bad-path"))
        assert "error" in result
        assert "Invalid golden_path" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_zip_data(self):
        result = json.loads(await self.tool("", golden_path="nextjs-fullstack"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_base64(self):
        result = json.loads(await self.tool("not-valid-base64!!!", golden_path="nextjs-fullstack"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_not_a_zip(self):
        not_a_zip = base64.b64encode(b"just some text").decode()
        result = json.loads(await self.tool(not_a_zip, golden_path="nextjs-fullstack"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_asset_files_classified_separately(self):
        files = {**SAMPLE_FILES, "assets/logo.svg": "<svg/>", "assets/hero.png": "PNG_BYTES"}
        b64 = _make_zip(files)
        result = json.loads(await self.tool(b64, golden_path="nextjs-fullstack"))
        assert result["summary"]["assets"] == 2

    @pytest.mark.asyncio
    async def test_component_filenames_in_manifest(self):
        result = json.loads(await self.tool(SAMPLE_ZIP_B64, golden_path="nextjs-fullstack"))
        manifest = json.loads(
            (pathlib.Path(result["_nexus_cache"]) / "01_manifest.json").read_text()
        )
        filenames = [c["filename"] for c in manifest["components"]]
        assert "components/Button.tsx" in filenames
        assert "components/Card.tsx" in filenames

    @pytest.mark.asyncio
    async def test_all_golden_paths_accepted(self):
        for path in ["nextjs-fullstack", "nextjs-static", "t3-stack", "vite-spa", "monorepo", "full-stack-rn"]:
            result = json.loads(await self.tool(SAMPLE_ZIP_B64, golden_path=path))
            assert "error" not in result, f"Failed for golden_path={path}"


# ══════════════════════════════════════════════════════════════════════════════
# 2. remap_to_golden_path
# ══════════════════════════════════════════════════════════════════════════════

class TestRemapToGoldenPath:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.tool = _extract_tool(register_remap_tool)

    @pytest.mark.asyncio
    async def test_returns_queue(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        assert "error" not in result
        assert "queue_files" in result
        assert len(result["queue_files"]) > 0

    @pytest.mark.asyncio
    async def test_returns_nexus_cache(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        assert "_nexus_cache" in result

    @pytest.mark.asyncio
    async def test_file_tree_written_to_cache(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        file_tree_path = pathlib.Path(result["_nexus_cache"]) / "04_file_tree.json"
        assert file_tree_path.exists()
        file_tree = json.loads(file_tree_path.read_text())
        assert "files" in file_tree
        assert len(file_tree["files"]) > 0

    @pytest.mark.asyncio
    async def test_file_tree_has_path_and_content(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        file_tree = json.loads(
            (pathlib.Path(result["_nexus_cache"]) / "04_file_tree.json").read_text()
        )
        for f in file_tree["files"]:
            assert "path" in f
            assert "content" in f

    @pytest.mark.asyncio
    async def test_globals_css_in_file_tree(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        file_tree = json.loads(
            (pathlib.Path(result["_nexus_cache"]) / "04_file_tree.json").read_text()
        )
        paths = [f["path"] for f in file_tree["files"]]
        assert any("globals.css" in p for p in paths)

    @pytest.mark.asyncio
    async def test_package_json_in_file_tree(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        file_tree = json.loads(
            (pathlib.Path(result["_nexus_cache"]) / "04_file_tree.json").read_text()
        )
        paths = [f["path"] for f in file_tree["files"]]
        assert any("package.json" in p for p in paths)

    @pytest.mark.asyncio
    async def test_tsconfig_in_file_tree(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        file_tree = json.loads(
            (pathlib.Path(result["_nexus_cache"]) / "04_file_tree.json").read_text()
        )
        paths = [f["path"] for f in file_tree["files"]]
        assert any("tsconfig.json" in p for p in paths)

    @pytest.mark.asyncio
    async def test_queue_files_written_to_disk(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        queue_dir = pathlib.Path(result["queue_dir"])
        assert queue_dir.exists()
        for filename in result["queue_files"]:
            assert (queue_dir / filename).exists()

    @pytest.mark.asyncio
    async def test_queue_items_metadata_only(self):
        """queue_items contains filename+path only — content is read from disk to keep response slim."""
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        assert "queue_items" in result
        assert len(result["queue_items"]) == len(result["queue_files"])
        for item in result["queue_items"]:
            assert "filename" in item
            assert "path" in item
            assert "content" not in item  # content intentionally omitted from response
            # but the file must exist on disk and have content
            assert pathlib.Path(item["path"]).exists()
            assert len(pathlib.Path(item["path"]).read_text()) > 0

    @pytest.mark.asyncio
    async def test_user_prompt_accepted(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest, user_prompt="Add dark mode support"))
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_project_name_in_result(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        assert "project_name" in result

    @pytest.mark.asyncio
    async def test_invalid_json_returns_error(self):
        result = json.loads(await self.tool("not json"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_golden_path_in_result(self):
        manifest = await _make_manifest()
        result = json.loads(await self.tool(manifest))
        assert "golden_path" in result
        assert result["golden_path"] == "nextjs-fullstack"


# ══════════════════════════════════════════════════════════════════════════════
# 3. package_output
# ══════════════════════════════════════════════════════════════════════════════

class TestPackageOutput:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.tool = _extract_tool(register_package_tool)

    @pytest.mark.asyncio
    async def test_returns_zip_path(self):
        file_tree = await _make_file_tree()
        result = json.loads(await self.tool(file_tree))
        assert "error" not in result
        assert "zip_path" in result
        assert pathlib.Path(result["zip_path"]).exists()

    @pytest.mark.asyncio
    async def test_zip_contains_files(self):
        file_tree = await _make_file_tree()
        result = json.loads(await self.tool(file_tree))
        with zipfile.ZipFile(result["zip_path"]) as zf:
            names = zf.namelist()
        assert len(names) > 0

    @pytest.mark.asyncio
    async def test_total_files_count_matches(self):
        file_tree = await _make_file_tree()
        result = json.loads(await self.tool(file_tree))
        with zipfile.ZipFile(result["zip_path"]) as zf:
            assert len(zf.namelist()) == result["total_files"]

    @pytest.mark.asyncio
    async def test_size_bytes_reported(self):
        file_tree = await _make_file_tree()
        result = json.loads(await self.tool(file_tree))
        assert "size_bytes" in result
        assert result["size_bytes"] > 0

    @pytest.mark.asyncio
    async def test_project_name_in_result(self):
        file_tree = await _make_file_tree()
        result = json.loads(await self.tool(file_tree))
        assert "project_name" in result

    @pytest.mark.asyncio
    async def test_empty_file_list_returns_error(self):
        empty_tree = json.dumps({"project_name": "test", "golden_path": "nextjs-fullstack", "files": []})
        result = json.loads(await self.tool(empty_tree))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_json_returns_error(self):
        result = json.loads(await self.tool("bad json"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_error_file_tree_propagated(self):
        err = json.dumps({"error": "upstream fail"})
        result = json.loads(await self.tool(err))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_full_pipeline_end_to_end(self):
        """Integration test: ingest → remap → package."""
        ingest = _extract_tool(register_ingest_tool)
        remap = _extract_tool(register_remap_tool)
        package = _extract_tool(register_package_tool)

        manifest = await ingest(SAMPLE_ZIP_B64, golden_path="nextjs-fullstack", project_name="e2e-test")
        assert "error" not in json.loads(manifest)

        file_tree = await remap(manifest)
        assert "error" not in json.loads(file_tree)

        output = json.loads(await package(file_tree))
        assert "error" not in output
        assert output["project_name"] == "e2e-test"
        assert output["total_files"] > 0

        assert pathlib.Path(output["zip_path"]).exists()
        with zipfile.ZipFile(output["zip_path"]) as zf:
            assert zipfile.is_zipfile(output["zip_path"])
            assert len(zf.namelist()) > 0


# ══════════════════════════════════════════════════════════════════════════════
# 4. update_file_in_tree
# ══════════════════════════════════════════════════════════════════════════════

from tools.figma.filetree import register_filetree_tool


class TestUpdateFileInTree:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.tool = _extract_tool(register_filetree_tool)

    @pytest.mark.asyncio
    async def test_updates_existing_entry(self):
        file_tree = await _make_file_tree()
        remap = json.loads(file_tree)
        cache = remap["_nexus_cache"]
        # Pick the first queue item path
        first_path = remap["queue_items"][0]["filename"].replace(".md", ".tsx")
        # Use an actual path from the file tree
        tree = json.loads((pathlib.Path(cache) / "04_file_tree.json").read_text())
        existing_path = tree["files"][0]["path"]

        result = json.loads(await self.tool(
            path=existing_path,
            content="// transformed content",
            nexus_cache=cache,
        ))
        assert result["ok"] is True
        assert result["path"] == existing_path

        # Verify it was written
        updated = json.loads((pathlib.Path(cache) / "04_file_tree.json").read_text())
        match = next(f for f in updated["files"] if f["path"] == existing_path)
        assert match["content"] == "// transformed content"

    @pytest.mark.asyncio
    async def test_appends_new_entry(self):
        file_tree = await _make_file_tree()
        cache = json.loads(file_tree)["_nexus_cache"]

        result = json.loads(await self.tool(
            path="components/new-component.tsx",
            content="export function NewComponent() {}",
            nexus_cache=cache,
        ))
        assert result["ok"] is True

        updated = json.loads((pathlib.Path(cache) / "04_file_tree.json").read_text())
        paths = [f["path"] for f in updated["files"]]
        assert "components/new-component.tsx" in paths

    @pytest.mark.asyncio
    async def test_missing_cache_returns_error(self):
        result = json.loads(await self.tool(
            path="some/file.tsx",
            content="content",
            nexus_cache="/tmp/nexus-does-not-exist-xyz",
        ))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_does_not_affect_other_files(self):
        file_tree = await _make_file_tree()
        cache = json.loads(file_tree)["_nexus_cache"]
        tree_before = json.loads((pathlib.Path(cache) / "04_file_tree.json").read_text())
        count_before = len(tree_before["files"])

        # Update an existing file — count should stay the same
        existing_path = tree_before["files"][0]["path"]
        await self.tool(path=existing_path, content="new content", nexus_cache=cache)

        tree_after = json.loads((pathlib.Path(cache) / "04_file_tree.json").read_text())
        assert len(tree_after["files"]) == count_before


# ── ingest_from_prompt tests ──────────────────────────────────────────────────

from tools.figma.prompt_ingest import register_prompt_ingest_tool, _infer_components, _hint_for


_prompt_ingest = _extract_tool(register_prompt_ingest_tool)


class TestIngestFromPrompt:

    @pytest.mark.asyncio
    async def test_requires_description(self):
        result = json.loads(await _prompt_ingest(description="", golden_path="nextjs-static"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_requires_golden_path(self):
        result = json.loads(await _prompt_ingest(description="A landing page", golden_path=""))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_rejects_invalid_golden_path(self):
        result = json.loads(await _prompt_ingest(description="A landing page", golden_path="rails-app"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_returns_manifest_shape(self):
        result = json.loads(await _prompt_ingest(
            description="A SaaS landing page with a hero and footer",
            golden_path="nextjs-static",
            project_name="test-project",
        ))
        assert "error" not in result
        assert result["project_name"] == "test-project"
        assert result["golden_path"] == "nextjs-static"
        assert result["source_type"] == "prompt"
        assert "_nexus_cache" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_infers_components_from_description(self):
        result = json.loads(await _prompt_ingest(
            description="A landing page with a hero section and footer",
            golden_path="nextjs-static",
            project_name="test-infer",
        ))
        assert result["summary"]["components"] + result["summary"]["pages"] > 0
        assert result["total_files"] > 0

    @pytest.mark.asyncio
    async def test_explicit_pages_used(self):
        result = json.loads(await _prompt_ingest(
            description="Build this",
            golden_path="nextjs-static",
            project_name="test-explicit",
            pages=["HomePage", "AboutPage"],
            components=[],
        ))
        assert result["summary"]["pages"] == 2
        assert result["summary"]["components"] == 0

    @pytest.mark.asyncio
    async def test_explicit_components_used(self):
        result = json.loads(await _prompt_ingest(
            description="Build this",
            golden_path="nextjs-static",
            project_name="test-explicit-comp",
            pages=[],
            components=["HeroSection", "PricingSection", "Footer"],
        ))
        assert result["summary"]["components"] == 3
        assert result["summary"]["pages"] == 0

    @pytest.mark.asyncio
    async def test_scaffold_fallback_creates_one_page(self):
        """With no matching signals, should fall back to a single HomePage."""
        result = json.loads(await _prompt_ingest(
            description="scaffold a clean project",
            golden_path="nextjs-fullstack",
            project_name="test-scaffold",
        ))
        assert result["total_files"] >= 1

    @pytest.mark.asyncio
    async def test_writes_cache_file(self, tmp_path):
        result = json.loads(await _prompt_ingest(
            description="A simple portfolio site",
            golden_path="nextjs-static",
            project_name="test-cache",
        ))
        cache = pathlib.Path(result["_nexus_cache"]) / "01_manifest.json"
        assert cache.exists()
        manifest = json.loads(cache.read_text())
        assert manifest["source_type"] == "prompt"
        assert manifest["golden_path"] == "nextjs-static"


class TestInferComponents:

    def test_landing_page_infers_home_page(self):
        pages, _ = _infer_components("A landing page for our product")
        assert "HomePage" in pages

    def test_dashboard_inferred(self):
        pages, _ = _infer_components("An admin dashboard with charts")
        assert "DashboardPage" in pages

    def test_hero_inferred_as_component(self):
        _, components = _infer_components("A site with a big hero section")
        assert "HeroSection" in components

    def test_footer_inferred_as_component(self):
        _, components = _infer_components("Include a footer with links")
        assert "Footer" in components

    def test_no_signals_returns_fallback(self):
        pages, components = _infer_components("scaffold a clean project")
        assert pages == ["HomePage"]
        assert components == []

    def test_no_duplicates(self):
        pages, components = _infer_components(
            "A landing page homepage with a hero and hero banner"
        )
        all_names = pages + components
        assert len(all_names) == len(set(all_names))


class TestHintFor:

    def test_known_stem_returns_hint(self):
        assert "hero" in _hint_for("HeroSection").lower()

    def test_unknown_stem_returns_default(self):
        hint = _hint_for("WeirdComponentXYZ")
        assert len(hint) > 0  # returns _DEFAULT_HINT, not empty


# ── ingest_from_codebase tests ────────────────────────────────────────────────

from tools.figma.codebase_ingest import register_codebase_ingest_tool

_codebase_ingest = _extract_tool(register_codebase_ingest_tool)


class TestIngestFromCodebase:

    @pytest.mark.asyncio
    async def test_requires_project_dir(self):
        result = json.loads(await _codebase_ingest(project_dir="", golden_path="nextjs-static"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_requires_golden_path(self, tmp_path):
        result = json.loads(await _codebase_ingest(project_dir=str(tmp_path), golden_path=""))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_rejects_nonexistent_dir(self):
        result = json.loads(await _codebase_ingest(
            project_dir="/nonexistent/path/xyz", golden_path="nextjs-static"
        ))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_rejects_invalid_golden_path(self, tmp_path):
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path), golden_path="rails-app"
        ))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_errors_on_empty_source_dir(self, tmp_path):
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static"
        ))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_reads_tsx_files(self, tmp_path):
        (tmp_path / "HeroSection.tsx").write_text(
            "export function HeroSection() { return <section>Hello</section>; }"
        )
        (tmp_path / "Footer.tsx").write_text(
            "export function Footer() { return <footer>Footer</footer>; }"
        )
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static"
        ))
        assert "error" not in result
        assert result["source_type"] == "codebase"
        assert result["summary"]["components"] == 2

    @pytest.mark.asyncio
    async def test_skips_config_files(self, tmp_path):
        (tmp_path / "HeroSection.tsx").write_text("export function HeroSection() { return <div/>; }")
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}')
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static"
        ))
        assert result["summary"]["components"] == 1
        assert result["summary"]["skipped_config"] >= 2

    @pytest.mark.asyncio
    async def test_skips_node_modules(self, tmp_path):
        (tmp_path / "HeroSection.tsx").write_text("export function HeroSection() { return <div/>; }")
        nm = tmp_path / "node_modules" / "react"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = require('./cjs/react.development.js');")
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static"
        ))
        assert result["summary"]["components"] == 1

    @pytest.mark.asyncio
    async def test_classifies_page_files(self, tmp_path):
        (tmp_path / "HomePage.tsx").write_text("export function HomePage() { return <main/>; }")
        (tmp_path / "Button.tsx").write_text("export function Button() { return <button/>; }")
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static"
        ))
        assert result["summary"]["pages"] == 1
        assert result["summary"]["components"] == 1

    @pytest.mark.asyncio
    async def test_defaults_project_name_to_dir_name(self, tmp_path):
        (tmp_path / "App.tsx").write_text("export function App() { return <div/>; }")
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static"
        ))
        assert result["project_name"] == tmp_path.name

    @pytest.mark.asyncio
    async def test_returns_manifest_shape(self, tmp_path):
        (tmp_path / "HeroSection.tsx").write_text("export function HeroSection() { return <div/>; }")
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path),
            golden_path="nextjs-static",
            project_name="my-migration",
        ))
        assert result["project_name"] == "my-migration"
        assert result["golden_path"] == "nextjs-static"
        assert result["source_type"] == "codebase"
        assert "source_dir" in result
        assert "_nexus_cache" in result

    @pytest.mark.asyncio
    async def test_writes_cache_file(self, tmp_path):
        (tmp_path / "HeroSection.tsx").write_text("export function HeroSection() { return <div/>; }")
        result = json.loads(await _codebase_ingest(
            project_dir=str(tmp_path),
            golden_path="nextjs-static",
            project_name="test-cache-cb",
        ))
        cache = pathlib.Path(result["_nexus_cache"]) / "01_manifest.json"
        assert cache.exists()
        manifest = json.loads(cache.read_text())
        assert manifest["source_type"] == "codebase"
        assert manifest["source_dir"] == str(tmp_path)
