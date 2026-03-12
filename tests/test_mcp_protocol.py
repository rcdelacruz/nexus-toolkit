"""
MCP protocol-layer tests.

These tests call tools through FastMCP.call_tool() — the same dispatch path
used by any real MCP client (Claude Code, n8n, Cursor, etc.).

This exercises things _extract_tool() bypasses entirely:
  - Tool registration (names, schemas)
  - Argument parsing and validation by FastMCP
  - TextContent serialization of the response
  - The mcp.call_tool() dispatch chain

Tests are intentionally narrow and fast — they validate the protocol layer,
not the business logic (which is covered by test_figma_pipeline.py and
test_improvements.py).
"""

import base64
import io
import pathlib
import json
import zipfile
from typing import Any

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from tools.figma import register_figma_tools


# ── shared server fixture ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def mcp_server() -> FastMCP:
    """A single FastMCP instance with all figma tools registered, shared across tests."""
    server = FastMCP("nexus-test")
    register_figma_tools(server)
    return server


def _parse(result: Any) -> dict:
    """
    Extract the JSON dict from a call_tool response.

    call_tool returns: (list[ContentBlock], raw_dict)
    The first ContentBlock is TextContent with the tool's JSON string output.
    """
    blocks, _ = result
    assert len(blocks) >= 1, "Expected at least one content block"
    block = blocks[0]
    assert isinstance(block, TextContent), f"Expected TextContent, got {type(block)}"
    return json.loads(block.text)


def _make_zip(*files: tuple[str, str]) -> str:
    """Build an in-memory ZIP and return base64."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files:
            zf.writestr(name, content)
    return base64.b64encode(buf.getvalue()).decode()


# ── 1. Tool registration ───────────────────────────────────────────────────────

class TestToolRegistration:
    """Verify all seven tools are registered under the correct MCP names."""

    EXPECTED_TOOLS = {
        "ingest_figma_zip",
        "ingest_from_prompt",
        "ingest_from_codebase",
        "remap_to_golden_path",
        "validate_output",
        "package_output",
        "update_file_in_tree",
    }

    @pytest.mark.asyncio
    async def test_all_tools_registered(self, mcp_server):
        tools = await mcp_server.list_tools()
        registered = {t.name for t in tools}
        missing = self.EXPECTED_TOOLS - registered
        assert missing == set(), f"Tools not registered: {missing}"

    @pytest.mark.asyncio
    async def test_no_extra_unexpected_tools(self, mcp_server):
        """Catch accidental double-registration or leaked test tools."""
        tools = await mcp_server.list_tools()
        registered = {t.name for t in tools}
        unexpected = registered - self.EXPECTED_TOOLS
        assert unexpected == set(), f"Unexpected tools registered: {unexpected}"

    @pytest.mark.asyncio
    async def test_each_tool_has_description(self, mcp_server):
        tools = await mcp_server.list_tools()
        for t in tools:
            assert t.description and len(t.description.strip()) > 10, (
                f"Tool '{t.name}' has no meaningful description"
            )

    @pytest.mark.asyncio
    async def test_each_tool_has_input_schema(self, mcp_server):
        tools = await mcp_server.list_tools()
        for t in tools:
            assert t.inputSchema, f"Tool '{t.name}' has no input schema"


# ── 2. Response format ────────────────────────────────────────────────────────

class TestResponseFormat:
    """
    Every tool must return TextContent wrapping a valid JSON string.
    The MCP client (Claude Code) json.loads() the text to get the result.
    """

    @pytest.mark.asyncio
    async def test_ingest_returns_text_content(self, mcp_server):
        zip_b64 = _make_zip(
            ("components/Hero.tsx", "export function Hero() { return <section/>; }")
        )
        result = await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "format-test",
        })
        blocks, _ = result
        assert len(blocks) == 1
        assert isinstance(blocks[0], TextContent)
        # Must be parseable JSON
        parsed = json.loads(blocks[0].text)
        assert isinstance(parsed, dict)

    @pytest.mark.asyncio
    async def test_error_response_is_also_json(self, mcp_server):
        """Even errors come back as JSON inside TextContent, not as exceptions."""
        result = await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": "not-valid-base64!!!",
            "golden_path": "nextjs-static",
        })
        parsed = _parse(result)
        # Should have an "error" key, not raise an exception
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_remap_returns_text_content(self, mcp_server):
        zip_b64 = _make_zip(
            ("components/Hero.tsx", "export function Hero() { return <section/>; }")
        )
        manifest = _parse(await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "remap-format-test",
        }))
        result = await mcp_server.call_tool("remap_to_golden_path", {
            "manifest_json": json.dumps(manifest),
        })
        blocks, _ = result
        assert isinstance(blocks[0], TextContent)
        parsed = json.loads(blocks[0].text)
        assert isinstance(parsed, dict)


# ── 3. Argument passing through the MCP layer ────────────────────────────────

class TestArgumentPassing:
    """
    Verify arguments are correctly routed through FastMCP's dispatch —
    especially that optional parameters work and wrong types fail cleanly.
    """

    @pytest.mark.asyncio
    async def test_project_name_flows_through(self, mcp_server):
        zip_b64 = _make_zip(("components/Card.tsx", "export function Card() {}"))
        result = _parse(await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "my-unique-name",
        }))
        assert result["project_name"] == "my-unique-name"

    @pytest.mark.asyncio
    async def test_golden_path_flows_through(self, mcp_server):
        zip_b64 = _make_zip(("components/Card.tsx", "export function Card() {}"))
        result = _parse(await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "t3-stack",
            "project_name": "gp-test",
        }))
        assert result["golden_path"] == "t3-stack"

    @pytest.mark.asyncio
    async def test_user_prompt_optional_in_remap(self, mcp_server):
        """user_prompt is optional — omitting it must not crash."""
        zip_b64 = _make_zip(("components/Hero.tsx", "export function Hero() {}"))
        manifest_raw = await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "no-prompt-test",
        })
        manifest = _parse(manifest_raw)
        # Call remap WITHOUT user_prompt — should work fine
        result = _parse(await mcp_server.call_tool("remap_to_golden_path", {
            "manifest_json": json.dumps(manifest),
        }))
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_user_prompt_with_extra_instructions(self, mcp_server):
        """user_prompt is forwarded to queue files."""
        zip_b64 = _make_zip(("components/Hero.tsx", "export function Hero() {}"))
        manifest = _parse(await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "prompt-test",
        }))
        result = _parse(await mcp_server.call_tool("remap_to_golden_path", {
            "manifest_json": json.dumps(manifest),
            "user_prompt": "Use Inter font throughout",
        }))
        assert "error" not in result
        # The prompt should appear in at least one queue file on disk
        queue_items = result.get("queue_items", [])
        if queue_items:
            combined = " ".join(
                pathlib.Path(item["path"]).read_text() for item in queue_items
            )
            assert "Inter" in combined

    @pytest.mark.asyncio
    async def test_project_dir_argument_for_codebase_ingest(self, mcp_server, tmp_path):
        (tmp_path / "Hero.tsx").write_text("export function Hero() { return <section/>; }")
        result = _parse(await mcp_server.call_tool("ingest_from_codebase", {
            "project_dir": str(tmp_path),
            "golden_path": "nextjs-static",
            "project_name": "codebase-arg-test",
        }))
        assert "error" not in result
        assert result["project_name"] == "codebase-arg-test"
        assert result["source_type"] == "codebase"


# ── 4. Full pipeline through MCP calls ───────────────────────────────────────

class TestMCPPipeline:
    """
    ingest → remap → validate through mcp.call_tool() the whole way.
    This is the same sequence a real MCP client would execute.
    """

    HERO_SOURCE = (
        '"use client";\n'
        'export function Hero() {\n'
        '  return (\n'
        '    <section className="py-24">\n'
        '      <h1 className="text-5xl font-bold">Hello World</h1>\n'
        '    </section>\n'
        '  );\n'
        '}\n'
    )

    @pytest.mark.asyncio
    async def test_ingest_remap_via_mcp(self, mcp_server):
        zip_b64 = _make_zip(
            ("components/Hero.tsx", self.HERO_SOURCE),
            ("styles/globals.css", ":root { --primary: hsl(210 100% 50%); }"),
        )
        # Step 1: ingest
        manifest = _parse(await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "pipeline-mcp-test",
        }))
        assert "error" not in manifest
        assert manifest["golden_path"] == "nextjs-static"

        # Step 2: remap
        remap = _parse(await mcp_server.call_tool("remap_to_golden_path", {
            "manifest_json": json.dumps(manifest),
        }))
        assert "error" not in remap
        assert remap["queue_count"] > 0
        assert "_nexus_cache" in remap
        assert "passthrough_paths" not in remap  # passthrough_paths lives in file tree, not summary

    @pytest.mark.asyncio
    async def test_validate_no_missing_required_after_remap(self, mcp_server):
        """Core regression: validate must pass with 0 MISSING_REQUIRED after reference fix."""
        zip_b64 = _make_zip(
            ("components/Hero.tsx", self.HERO_SOURCE),
        )
        manifest = _parse(await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "validate-mcp-test",
        }))
        remap = _parse(await mcp_server.call_tool("remap_to_golden_path", {
            "manifest_json": json.dumps(manifest),
        }))
        validate = _parse(await mcp_server.call_tool("validate_output", {
            "file_tree_json": json.dumps({
                "project_name": "validate-mcp-test",
                "golden_path": "nextjs-static",
                "_nexus_cache": remap["_nexus_cache"],
            }),
        }))
        missing = [e for e in validate.get("errors", []) if e.startswith("MISSING_REQUIRED")]
        assert missing == [], (
            f"MISSING_REQUIRED errors after reference fix — lib/utils.ts etc. not seeded:\n"
            + "\n".join(missing)
        )

    @pytest.mark.asyncio
    async def test_validate_shadcn_passthrough_not_orphan_via_mcp(self, mcp_server):
        """
        shadcn primitive passed through ZIP ingest must get SHADCN_PASSTHROUGH,
        not ORPHAN_FILE, in the validate response.
        """
        shadcn_button = (
            '"use client";\n'
            'import { Slot } from "@radix-ui/react-slot@1.1.2";\n'
            'import { cn } from "./utils";\n'
            'export function Button({ className, children }) {\n'
            '  return <Slot className={cn(className)}>{children}</Slot>;\n'
            '}\n'
        )
        zip_b64 = _make_zip(
            ("components/Hero.tsx", self.HERO_SOURCE),
            ("components/ui/button.tsx", shadcn_button),
        )
        manifest = _parse(await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "shadcn-mcp-test",
        }))
        remap = _parse(await mcp_server.call_tool("remap_to_golden_path", {
            "manifest_json": json.dumps(manifest),
        }))
        validate = _parse(await mcp_server.call_tool("validate_output", {
            "file_tree_json": json.dumps({
                "project_name": "shadcn-mcp-test",
                "golden_path": "nextjs-static",
                "_nexus_cache": remap["_nexus_cache"],
            }),
        }))
        warnings = validate.get("warnings", [])
        # button.tsx was shadcn passthrough — must get SHADCN_PASSTHROUGH not ORPHAN_FILE
        orphan_for_button = [w for w in warnings if "ORPHAN_FILE" in w and "button" in w]
        shadcn_for_button = [w for w in warnings if "SHADCN_PASSTHROUGH" in w and "button" in w]
        assert orphan_for_button == [], f"button.tsx should not be ORPHAN_FILE: {orphan_for_button}"
        assert len(shadcn_for_button) == 1, f"button.tsx should be SHADCN_PASSTHROUGH: {warnings}"

    @pytest.mark.asyncio
    async def test_ingest_from_prompt_via_mcp(self, mcp_server):
        result = _parse(await mcp_server.call_tool("ingest_from_prompt", {
            "description": "A portfolio site with hero, skills, and contact sections",
            "golden_path": "nextjs-static",
            "project_name": "prompt-mcp-test",
        }))
        assert "error" not in result
        assert result["source_type"] == "prompt"
        assert result["golden_path"] == "nextjs-static"

    @pytest.mark.asyncio
    async def test_preflight_key_present_in_mcp_remap_result(self, mcp_server):
        """missing_required_preflight must be present in the remap response."""
        zip_b64 = _make_zip(("components/Hero.tsx", self.HERO_SOURCE))
        manifest = _parse(await mcp_server.call_tool("ingest_figma_zip", {
            "zip_base64": zip_b64,
            "golden_path": "nextjs-static",
            "project_name": "preflight-mcp-test",
        }))
        remap = _parse(await mcp_server.call_tool("remap_to_golden_path", {
            "manifest_json": json.dumps(manifest),
        }))
        assert "missing_required_preflight" in remap, (
            "remap_to_golden_path must expose missing_required_preflight "
            "so callers can see gaps without running validate_output"
        )
        # After our reference fix, this should be empty for nextjs-static
        assert remap["missing_required_preflight"] == [], (
            f"nextjs-static still has unseeded required files: "
            f"{remap['missing_required_preflight']}"
        )
