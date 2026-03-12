"""
Regression tests for the six pipeline improvements documented in
figma-make-to-golden-path-journey.md.

Covers:
  2a. lib/utils.ts (and other requiredFiles) now seeded from reference — no MISSING_REQUIRED
  2b. Header/Footer seeded from reference
  2c. Section classifier catches portfolio keywords + manifest signals
  2d. shadcn passthrough tagged → SHADCN_PASSTHROUGH not ORPHAN_FILE; inline-style suppressed
  2e. Radix/Recharts inline styles suppressed for passthrough files
  2f. Pre-flight surfaces missing required files in remap result
"""

import json
import pathlib
from unittest.mock import MagicMock

import pytest

from tools.figma.remap import _classify, register_remap_tool
from tools.figma.validate import _run_checks
from tools.figma.ingest import register_ingest_tool
from tools.figma.codebase_ingest import register_codebase_ingest_tool
from tools.figma.validate import register_validate_tool


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_tool(register_fn):
    captured = {}
    mock_mcp = MagicMock()
    mock_mcp.tool.return_value = lambda f: captured.setdefault("fn", f) or f
    register_fn(mock_mcp)
    return captured["fn"]


def _file(path: str, content: str) -> dict:
    return {"path": path, "content": content}


def _tree(*files, golden_path="nextjs-static", passthrough_paths=None) -> dict:
    return {
        "golden_path": golden_path,
        "files": list(files),
        "passthrough_paths": passthrough_paths or [],
    }


# ── 2c. Section classifier ─────────────────────────────────────────────────────

class TestSectionClassifier:
    """_classify() should route portfolio section names correctly."""

    # Manifest rules used for most tests (nextjs-static shape)
    RULES = {
        "categories": {
            "layout": {"outputPath": "components/layout/{ComponentName}.tsx",
                        "signals": ["Header", "Footer", "Navbar"]},
            "section": {"outputPath": "components/sections/{ComponentName}.tsx",
                        "signals": ["Hero", "Features", "Pricing"]},
            "ui":      {"outputPath": "components/ui/{ComponentName}.tsx",
                        "signals": ["Button", "Card"]},
        }
    }

    # ── original terms still work ────────────────────────────────────────────
    def test_hero_is_section(self):
        assert _classify("Hero", self.RULES, "nextjs-static") == "section"

    def test_pricing_is_section(self):
        assert _classify("Pricing", self.RULES, "nextjs-static") == "section"

    def test_contact_is_section(self):
        assert _classify("Contact", self.RULES, "nextjs-static") == "section"

    # ── newly added portfolio keywords (suggestion 2c) ───────────────────────
    def test_experience_is_section(self):
        assert _classify("Experience", self.RULES, "nextjs-static") == "section"

    def test_projects_is_section(self):
        assert _classify("Projects", self.RULES, "nextjs-static") == "section"

    def test_skills_is_section(self):
        assert _classify("Skills", self.RULES, "nextjs-static") == "section"

    def test_work_is_section(self):
        assert _classify("Work", self.RULES, "nextjs-static") == "section"

    def test_portfolio_is_section(self):
        assert _classify("Portfolio", self.RULES, "nextjs-static") == "section"

    def test_gallery_is_section(self):
        assert _classify("Gallery", self.RULES, "nextjs-static") == "section"

    def test_services_is_section(self):
        assert _classify("Services", self.RULES, "nextjs-static") == "section"

    def test_timeline_is_section(self):
        assert _classify("Timeline", self.RULES, "nextjs-static") == "section"

    def test_education_is_section(self):
        assert _classify("Education", self.RULES, "nextjs-static") == "section"

    def test_certifications_is_section(self):
        assert _classify("Certifications", self.RULES, "nextjs-static") == "section"

    # ── manifest signals for section also consulted (suggestion 2c) ──────────
    def test_manifest_section_signal_features_is_section(self):
        """'Features' is in manifest section.signals but not SECTION_KEYWORDS."""
        assert _classify("Features", self.RULES, "nextjs-static") == "section"

    # ── compound names containing keywords ───────────────────────────────────
    def test_compound_name_containing_experience(self):
        assert _classify("WorkExperience", self.RULES, "nextjs-static") == "section"

    def test_compound_name_containing_skills(self):
        assert _classify("TechSkills", self.RULES, "nextjs-static") == "section"

    # ── other categories still classified correctly ───────────────────────────
    def test_button_is_ui(self):
        assert _classify("Button", self.RULES, "nextjs-static") == "ui"

    def test_card_is_ui(self):
        assert _classify("Card", self.RULES, "nextjs-static") == "ui"

    def test_header_is_layout(self):
        assert _classify("Header", self.RULES, "nextjs-static") == "layout"

    def test_footer_is_layout(self):
        assert _classify("Footer", self.RULES, "nextjs-static") == "layout"

    def test_app_is_root_page(self):
        assert _classify("app", self.RULES, "nextjs-static") == "root_page"

    def test_utils_is_discarded(self):
        assert _classify("utils", self.RULES, "nextjs-static") == "discard"


# ── 2d. SHADCN_PASSTHROUGH vs ORPHAN_FILE ────────────────────────────────────

class TestPassthroughVsOrphan:
    """Unreachable shadcn files should emit SHADCN_PASSTHROUGH, not ORPHAN_FILE."""

    # Minimal reachable tree: a page that imports nothing from ui/
    PAGE_CONTENT = (
        '"use client";\n'
        'export default function Page() { return <main>Hello</main>; }'
    )

    def test_orphan_shadcn_file_becomes_shadcn_passthrough(self):
        files = [
            _file("app/page.tsx", self.PAGE_CONTENT),
            _file("components/ui/button.tsx", '"use client";\nexport function Button() {}'),
        ]
        tree = _tree(*files, passthrough_paths=["components/ui/button.tsx"])
        errors, warnings = _run_checks(files, "nextjs-static",
                                       passthrough_paths=set(tree["passthrough_paths"]))
        shadcn_warns = [w for w in warnings if w.startswith("SHADCN_PASSTHROUGH")]
        orphan_warns = [w for w in warnings if "ORPHAN_FILE" in w and "button" in w]
        assert len(shadcn_warns) == 1
        assert len(orphan_warns) == 0

    def test_genuinely_orphan_file_stays_orphan(self):
        """A non-passthrough unreachable file still gets ORPHAN_FILE."""
        files = [
            _file("app/page.tsx", self.PAGE_CONTENT),
            _file("components/sections/Unused.tsx", "export function Unused() {}"),
        ]
        tree = _tree(*files, passthrough_paths=[])
        errors, warnings = _run_checks(files, "nextjs-static",
                                       passthrough_paths=set(tree["passthrough_paths"]))
        orphan_warns = [w for w in warnings if "ORPHAN_FILE" in w and "Unused" in w]
        assert len(orphan_warns) == 1

    def test_multiple_passthrough_files_all_downgraded(self):
        """All shadcn primitives in passthrough_paths should become SHADCN_PASSTHROUGH."""
        shadcn_files = [
            "components/ui/button.tsx",
            "components/ui/card.tsx",
            "components/ui/input.tsx",
        ]
        files = [
            _file("app/page.tsx", self.PAGE_CONTENT),
            *[_file(p, '"use client";\nexport function X() {}') for p in shadcn_files],
        ]
        errors, warnings = _run_checks(files, "nextjs-static",
                                       passthrough_paths=set(shadcn_files))
        shadcn_warns = [w for w in warnings if w.startswith("SHADCN_PASSTHROUGH")]
        orphan_warns = [w for w in warnings if "ORPHAN_FILE" in w]
        assert len(shadcn_warns) == 3
        assert len(orphan_warns) == 0


# ── 2e. Inline style suppressed for passthrough files ────────────────────────

class TestInlineStyleSuppressionForPassthrough:
    """Radix/Recharts inline styles in passthrough files must not emit FIGMA_ARTIFACT."""

    PAGE = 'export default function Page() { return <main/>; }'

    # Radix progress bar pattern
    PROGRESS_CONTENT = (
        '"use client";\n'
        'export function Progress({ value }: { value: number }) {\n'
        '  return (\n'
        '    <div>\n'
        '      <div style={{ transform: `translateX(-${100 - (value || 0)}%)` }} />\n'
        '    </div>\n'
        '  );\n'
        '}\n'
    )

    # Recharts chart pattern
    CHART_CONTENT = (
        '"use client";\n'
        'export function Chart({ color }: { color: string }) {\n'
        '  return <div style={{ "--color-bg": color } as React.CSSProperties} />;\n'
        '}\n'
    )

    def test_radix_progress_inline_style_suppressed_for_passthrough(self):
        files = [
            _file("app/page.tsx", self.PAGE),
            _file("components/ui/progress.tsx", self.PROGRESS_CONTENT),
        ]
        errors, warnings = _run_checks(
            files, "nextjs-static",
            passthrough_paths={"components/ui/progress.tsx"},
        )
        figma_warns = [w for w in warnings if "FIGMA_ARTIFACT" in w and "progress" in w]
        assert len(figma_warns) == 0

    def test_recharts_chart_inline_style_suppressed_for_passthrough(self):
        files = [
            _file("app/page.tsx", self.PAGE),
            _file("components/ui/chart.tsx", self.CHART_CONTENT),
        ]
        errors, warnings = _run_checks(
            files, "nextjs-static",
            passthrough_paths={"components/ui/chart.tsx"},
        )
        figma_warns = [w for w in warnings if "FIGMA_ARTIFACT" in w and "chart" in w]
        assert len(figma_warns) == 0

    def test_inline_style_in_non_passthrough_file_still_warned(self):
        """A transformed component with inline styles should still trigger the warning."""
        files = [
            _file("app/page.tsx", self.PAGE),
            _file("components/sections/Hero.tsx",
                  'export function Hero() { return <div style={{color:"red"}}/>; }'),
        ]
        errors, warnings = _run_checks(files, "nextjs-static", passthrough_paths=set())
        figma_warns = [w for w in warnings if "FIGMA_ARTIFACT" in w and "Hero" in w]
        assert len(figma_warns) == 1


# ── 2a + 2b. Golden path reference completeness ───────────────────────────────

class TestGoldenPathReferenceCompleteness:
    """Every file in requiredFiles must exist in the reference/ directory."""

    NEXUS_ROOT = pathlib.Path(__file__).parent.parent
    GOLDEN_PATHS_DIR = NEXUS_ROOT / "golden_paths"

    def _check_golden_path(self, name: str):
        ref_dir = self.GOLDEN_PATHS_DIR / name / "reference"
        manifest_path = self.GOLDEN_PATHS_DIR / name / "manifest.json"
        if not manifest_path.exists():
            pytest.skip(f"No manifest for {name}")
        ref_files = {
            f.relative_to(ref_dir).as_posix()
            for f in ref_dir.rglob("*") if f.is_file()
        }
        manifest = json.loads(manifest_path.read_text())
        required = manifest.get("requiredFiles", [])
        missing = [r for r in required if r not in ref_files]
        assert missing == [], (
            f"{name}: requiredFiles not in reference/: {missing}\n"
            f"Fix: add these files to golden_paths/{name}/reference/"
        )

    def test_nextjs_static_reference_complete(self):
        self._check_golden_path("nextjs-static")

    def test_nextjs_fullstack_reference_complete(self):
        self._check_golden_path("nextjs-fullstack")

    def test_t3_stack_reference_complete(self):
        self._check_golden_path("t3-stack")

    def test_vite_spa_reference_complete(self):
        self._check_golden_path("vite-spa")

    def test_monorepo_reference_complete(self):
        self._check_golden_path("monorepo")

    def test_full_stack_rn_reference_complete(self):
        self._check_golden_path("full-stack-rn")

    def test_full_stack_flutter_reference_complete(self):
        self._check_golden_path("full-stack-flutter")


# ── Phase 1 validate.py checks 17-20 ─────────────────────────────────────────


class TestPhase1ValidationChecks:
    """New checks 17-20 added in Phase 1 enterprise readiness."""

    # ── Check 17: Missing error boundary ─────────────────────────────────────

    def test_check17_warns_on_missing_error_tsx(self):
        """nextjs-fullstack without app/error.tsx should emit MISSING_ERROR_BOUNDARY warning."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_ERROR_BOUNDARY" in w for w in warnings)

    def test_check17_warns_on_missing_not_found(self):
        """nextjs-fullstack without app/not-found.tsx should emit MISSING_NOT_FOUND warning."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_NOT_FOUND" in w for w in warnings)

    def test_check17_no_warning_when_error_tsx_present(self):
        """No MISSING_ERROR_BOUNDARY warning when app/error.tsx is present."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
            {"path": "app/error.tsx", "content": '"use client"\nexport default function Error() {}'},
            {"path": "app/not-found.tsx", "content": "export default function NotFound() {}"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("MISSING_ERROR_BOUNDARY" in w for w in warnings)

    def test_check17_t3_stack_uses_src_prefix(self):
        """t3-stack should look for src/app/error.tsx, not app/error.tsx."""
        files = [
            {"path": "src/app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "src/app/globals.css", "content": "@import 'tailwindcss';"},
            {"path": "src/app/error.tsx", "content": '"use client"\nexport default function Error() {}'},
            {"path": "src/app/not-found.tsx", "content": "export default function NotFound() {}"},
        ]
        _, warnings = _run_checks(files, "t3-stack")
        assert not any("MISSING_ERROR_BOUNDARY" in w for w in warnings)

    def test_check17_not_triggered_for_vite_spa(self):
        """vite-spa is not a Next.js path — no MISSING_ERROR_BOUNDARY warning."""
        files = [
            {"path": "src/main.tsx", "content": "import './styles/globals.css'"},
            {"path": "src/styles/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "vite-spa")
        assert not any("MISSING_ERROR_BOUNDARY" in w for w in warnings)

    # ── Check 18: Missing env.ts ──────────────────────────────────────────────

    def test_check18_warns_on_missing_env_ts_nextjs_fullstack(self):
        """nextjs-fullstack without lib/env.ts emits MISSING_ENV_VALIDATION."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_ENV_VALIDATION" in w for w in warnings)

    def test_check18_no_warning_when_env_ts_present(self):
        """No MISSING_ENV_VALIDATION when lib/env.ts exists."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
            {"path": "lib/env.ts", "content": 'import { z } from "zod"'},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("MISSING_ENV_VALIDATION" in w for w in warnings)

    def test_check18_vite_spa_uses_src_lib_env(self):
        """vite-spa expects src/lib/env.ts."""
        files = [
            {"path": "src/main.tsx", "content": ""},
            {"path": "src/styles/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "vite-spa")
        assert any("MISSING_ENV_VALIDATION" in w for w in warnings)

    # ── Check 19: Missing logger.ts ───────────────────────────────────────────

    def test_check19_warns_on_missing_logger_ts(self):
        """nextjs-fullstack without lib/logger.ts emits MISSING_LOGGER."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_LOGGER" in w for w in warnings)

    def test_check19_no_warning_when_logger_present(self):
        """No MISSING_LOGGER when lib/logger.ts exists."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
            {"path": "lib/logger.ts", "content": 'import pino from "pino"'},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("MISSING_LOGGER" in w for w in warnings)

    def test_check19_not_triggered_for_nextjs_static(self):
        """nextjs-static (no server) does not require a logger."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "nextjs-static")
        assert not any("MISSING_LOGGER" in w for w in warnings)

    def test_check19_not_triggered_for_vite_spa(self):
        """vite-spa (client-only) does not require a logger."""
        files = [
            {"path": "src/main.tsx", "content": ""},
            {"path": "src/styles/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "vite-spa")
        assert not any("MISSING_LOGGER" in w for w in warnings)

    # ── Check 20: console.* in server code ────────────────────────────────────

    def test_check20_warns_console_in_api_route(self):
        """console.log in an API route emits SERVER_CONSOLE warning."""
        files = [
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
            {
                "path": "app/api/users/route.ts",
                "content": 'export async function GET() { console.log("hit"); return Response.json({}) }',
            },
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("SERVER_CONSOLE" in w for w in warnings)

    def test_check20_no_warning_in_client_component(self):
        """console.log in a "use client" component should not emit SERVER_CONSOLE."""
        files = [
            {"path": "app/globals.css", "content": "@import 'tailwindcss';"},
            {
                "path": "app/api/users/route.ts",
                "content": '"use client"\nexport function Foo() { console.log("x") }',
            },
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("SERVER_CONSOLE" in w for w in warnings)

    def test_check20_not_triggered_for_vite_spa(self):
        """vite-spa is client-only — no SERVER_CONSOLE check."""
        files = [
            {"path": "src/main.tsx", "content": ""},
            {"path": "src/styles/globals.css", "content": "@import 'tailwindcss';"},
            {
                "path": "src/api/client.ts",
                "content": 'console.log("debug")',
            },
        ]
        _, warnings = _run_checks(files, "vite-spa")
        assert not any("SERVER_CONSOLE" in w for w in warnings)

    # ── Check 21: Missing audit columns in Prisma schema ─────────────────────

    def test_check21_warns_on_missing_deleted_at(self):
        """nextjs-fullstack schema without deletedAt emits MISSING_AUDIT_COLUMNS."""
        files = [
            {
                "path": "prisma/schema.prisma",
                "content": 'model User { id String @id createdAt DateTime @default(now()) }',
            },
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_AUDIT_COLUMNS" in w and "deletedAt" in w for w in warnings)

    def test_check21_warns_on_missing_created_by_id(self):
        """nextjs-fullstack schema without createdById emits MISSING_AUDIT_COLUMNS."""
        files = [
            {
                "path": "prisma/schema.prisma",
                "content": 'model User { id String @id deletedAt DateTime? }',
            },
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_AUDIT_COLUMNS" in w and "createdById" in w for w in warnings)

    def test_check21_no_warning_when_audit_columns_present(self):
        """No MISSING_AUDIT_COLUMNS warning when schema has both deletedAt and createdById."""
        schema = (
            "model User { id String @id deletedAt DateTime? "
            "createdById String? updatedById String? }"
        )
        files = [{"path": "prisma/schema.prisma", "content": schema}]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("MISSING_AUDIT_COLUMNS" in w for w in warnings)

    def test_check21_t3_stack_uses_prisma_schema(self):
        """t3-stack also checks prisma/schema.prisma for audit columns."""
        files = [
            {
                "path": "prisma/schema.prisma",
                "content": 'model User { id String @id }',
            },
        ]
        _, warnings = _run_checks(files, "t3-stack")
        assert any("MISSING_AUDIT_COLUMNS" in w for w in warnings)

    def test_check21_monorepo_uses_packages_db_path(self):
        """monorepo checks packages/db/prisma/schema.prisma."""
        files = [
            {
                "path": "packages/db/prisma/schema.prisma",
                "content": 'model User { id String @id }',
            },
        ]
        _, warnings = _run_checks(files, "monorepo")
        assert any("MISSING_AUDIT_COLUMNS" in w for w in warnings)

    def test_check21_not_triggered_for_vite_spa(self):
        """vite-spa has no Prisma — MISSING_AUDIT_COLUMNS check is skipped."""
        files = [
            {"path": "src/main.tsx", "content": ""},
            {"path": "src/styles/globals.css", "content": "@import 'tailwindcss';"},
        ]
        _, warnings = _run_checks(files, "vite-spa")
        assert not any("MISSING_AUDIT_COLUMNS" in w for w in warnings)

    def test_check21_not_triggered_for_nextjs_static(self):
        """nextjs-static has no Prisma — MISSING_AUDIT_COLUMNS check is skipped."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
        ]
        _, warnings = _run_checks(files, "nextjs-static")
        assert not any("MISSING_AUDIT_COLUMNS" in w for w in warnings)

    def test_check21_no_warning_when_schema_absent(self):
        """No crash and no MISSING_AUDIT_COLUMNS when schema file is not in tree."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        # Schema is simply absent — check should not fire (no schema = different problem)
        assert not any("MISSING_AUDIT_COLUMNS" in w for w in warnings)

    # ── Check 22: Missing health endpoint ─────────────────────────────────────

    def test_check22_warns_on_missing_health_endpoint(self):
        """nextjs-fullstack without app/api/health/route.ts emits MISSING_HEALTH_ENDPOINT."""
        files = [{"path": "app/layout.tsx", "content": "export default function Layout() {}"}]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_HEALTH_ENDPOINT" in w for w in warnings)

    def test_check22_no_warning_when_health_present(self):
        """No MISSING_HEALTH_ENDPOINT when app/api/health/route.ts exists."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "app/api/health/route.ts", "content": "export function GET() {}"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("MISSING_HEALTH_ENDPOINT" in w for w in warnings)

    def test_check22_t3_stack_uses_src_app_path(self):
        """t3-stack expects src/app/api/health/route.ts."""
        files = [{"path": "src/app/layout.tsx", "content": ""}]
        _, warnings = _run_checks(files, "t3-stack")
        assert any("MISSING_HEALTH_ENDPOINT" in w for w in warnings)

    def test_check22_not_triggered_for_vite_spa(self):
        """vite-spa does not require a health endpoint."""
        files = [{"path": "src/main.tsx", "content": ""}]
        _, warnings = _run_checks(files, "vite-spa")
        assert not any("MISSING_HEALTH_ENDPOINT" in w for w in warnings)

    # ── Check 23: Missing instrumentation.ts ──────────────────────────────────

    def test_check23_warns_on_missing_instrumentation(self):
        """nextjs-fullstack without instrumentation.ts emits MISSING_INSTRUMENTATION."""
        files = [{"path": "app/layout.tsx", "content": "export default function Layout() {}"}]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_INSTRUMENTATION" in w for w in warnings)

    def test_check23_no_warning_when_instrumentation_present(self):
        """No MISSING_INSTRUMENTATION when instrumentation.ts exists."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "instrumentation.ts", "content": "export async function register() {}"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("MISSING_INSTRUMENTATION" in w for w in warnings)

    def test_check23_t3_stack_uses_src_path(self):
        """t3-stack expects src/instrumentation.ts."""
        files = [{"path": "src/app/layout.tsx", "content": ""}]
        _, warnings = _run_checks(files, "t3-stack")
        assert any("MISSING_INSTRUMENTATION" in w for w in warnings)

    def test_check23_monorepo_uses_apps_web_path(self):
        """monorepo expects apps/web/instrumentation.ts."""
        files = [{"path": "apps/web/app/layout.tsx", "content": ""}]
        _, warnings = _run_checks(files, "monorepo")
        assert any("MISSING_INSTRUMENTATION" in w for w in warnings)

    def test_check23_not_triggered_for_vite_spa(self):
        """vite-spa does not require instrumentation.ts."""
        files = [{"path": "src/main.tsx", "content": ""}]
        _, warnings = _run_checks(files, "vite-spa")
        assert not any("MISSING_INSTRUMENTATION" in w for w in warnings)

    # ── Check 24: Missing CSRF helper ─────────────────────────────────────────

    def test_check24_warns_on_missing_csrf_ts(self):
        """nextjs-fullstack without lib/csrf.ts emits MISSING_CSRF."""
        files = [{"path": "app/layout.tsx", "content": "export default function Layout() {}"}]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_CSRF" in w for w in warnings)

    def test_check24_no_warning_when_csrf_present(self):
        """No MISSING_CSRF when lib/csrf.ts exists."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "lib/csrf.ts", "content": "export function validateCsrfOrigin() {}"},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("MISSING_CSRF" in w for w in warnings)

    def test_check24_t3_stack_uses_src_lib(self):
        """t3-stack expects src/lib/csrf.ts."""
        files = [{"path": "src/app/layout.tsx", "content": ""}]
        _, warnings = _run_checks(files, "t3-stack")
        assert any("MISSING_CSRF" in w for w in warnings)

    def test_check24_not_triggered_for_vite_spa(self):
        """vite-spa (client-only) does not require csrf.ts."""
        files = [{"path": "src/main.tsx", "content": ""}]
        _, warnings = _run_checks(files, "vite-spa")
        assert not any("MISSING_CSRF" in w for w in warnings)

    def test_check24_not_triggered_for_nextjs_static(self):
        """nextjs-static (no server) does not require csrf.ts."""
        files = [{"path": "app/layout.tsx", "content": ""}]
        _, warnings = _run_checks(files, "nextjs-static")
        assert not any("MISSING_CSRF" in w for w in warnings)

    # ── Check 25: Missing sanitize helper ────────────────────────────────────

    def test_check25_warns_on_missing_sanitize_ts(self):
        """nextjs-fullstack without lib/sanitize.ts emits MISSING_SANITIZE."""
        files = [{"path": "app/layout.tsx", "content": "export default function Layout() {}"}]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert any("MISSING_SANITIZE" in w for w in warnings)

    def test_check25_no_warning_when_sanitize_present(self):
        """No MISSING_SANITIZE when lib/sanitize.ts exists."""
        files = [
            {"path": "app/layout.tsx", "content": "export default function Layout() {}"},
            {"path": "lib/sanitize.ts", "content": 'import DOMPurify from "isomorphic-dompurify"'},
        ]
        _, warnings = _run_checks(files, "nextjs-fullstack")
        assert not any("MISSING_SANITIZE" in w for w in warnings)

    def test_check25_monorepo_uses_apps_web_path(self):
        """monorepo expects apps/web/lib/sanitize.ts."""
        files = [{"path": "apps/web/app/layout.tsx", "content": ""}]
        _, warnings = _run_checks(files, "monorepo")
        assert any("MISSING_SANITIZE" in w for w in warnings)

    def test_check25_not_triggered_for_vite_spa(self):
        """vite-spa does not require sanitize.ts (no server check)."""
        files = [{"path": "src/main.tsx", "content": ""}]
        _, warnings = _run_checks(files, "vite-spa")
        assert not any("MISSING_SANITIZE" in w for w in warnings)


class TestRemapPreflightCheck:
    """remap_to_golden_path must expose missing_required_preflight in its result."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.remap = _extract_tool(register_remap_tool)
        self.ingest = _extract_tool(register_ingest_tool)
        self.codebase_ingest = _extract_tool(register_codebase_ingest_tool)

    @pytest.mark.asyncio
    async def test_preflight_key_present_in_result(self, tmp_path):
        (tmp_path / "Hero.tsx").write_text(
            "export function Hero() { return <section>Hello</section>; }"
        )
        manifest = await self.codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static", project_name="preflight-test"
        )
        result = json.loads(await self.remap(manifest))
        assert "missing_required_preflight" in result

    @pytest.mark.asyncio
    async def test_nextjs_static_preflight_empty_after_reference_fix(self, tmp_path):
        """After adding reference files, remap must seed ALL required files with no gaps."""
        (tmp_path / "Hero.tsx").write_text(
            "export function Hero() { return <section>Hello</section>; }"
        )
        manifest = await self.codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static", project_name="preflight-empty"
        )
        result = json.loads(await self.remap(manifest))
        missing = result.get("missing_required_preflight", ["MISSING_KEY"])
        assert missing == [], (
            f"nextjs-static still has unseeded required files after reference fix: {missing}"
        )

    @pytest.mark.asyncio
    async def test_passthrough_paths_written_to_file_tree(self):
        """
        shadcn passthrough only fires for source_type='figma' (ZIP ingest).
        The passthrough_paths list in 04_file_tree.json must be populated for
        any @radix-ui component that comes through the ZIP pipeline.
        """
        import base64, io, zipfile as _zipfile

        shadcn_source = (
            '"use client";\n'
            'import * as React from "react";\n'
            'import { Slot } from "@radix-ui/react-slot@1.1.2";\n'
            'import { cn } from "./utils";\n'
            'export function Button({ className, children }) {\n'
            '  return <Slot className={cn("btn", className)}>{children}</Slot>;\n'
            '}\n'
        )
        buf = io.BytesIO()
        with _zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("components/button.tsx", shadcn_source)
        zip_b64 = base64.b64encode(buf.getvalue()).decode()

        manifest = await self.ingest(
            zip_b64, golden_path="nextjs-static", project_name="passthrough-test"
        )
        result = json.loads(await self.remap(manifest))
        cache = pathlib.Path(result["_nexus_cache"])
        file_tree = json.loads((cache / "04_file_tree.json").read_text())

        passthrough = file_tree.get("passthrough_paths", [])
        assert isinstance(passthrough, list)
        assert any("button" in p for p in passthrough), (
            f"Expected button.tsx in passthrough_paths (radix-ui import should trigger passthrough). "
            f"Got: {passthrough}"
        )


# ── Integration: ingest → remap → validate passes clean for nextjs-static ────

class TestEndToEndValidation:
    """
    Full pipeline smoke test: a minimal portfolio ingest should pass validate_output
    with zero errors after our fixes (no MISSING_REQUIRED, no cascading BROKEN_IMPORTs).
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.codebase_ingest = _extract_tool(register_codebase_ingest_tool)
        self.remap = _extract_tool(register_remap_tool)
        self.validate = _extract_tool(register_validate_tool)

    @pytest.mark.asyncio
    async def test_no_missing_required_after_remap(self, tmp_path):
        """After remap, all nextjs-static requiredFiles are present in the file tree."""
        (tmp_path / "Hero.tsx").write_text(
            "export function Hero() { return <section>Hero</section>; }"
        )
        manifest = await self.codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static", project_name="e2e-validate"
        )
        remap_result = json.loads(await self.remap(manifest))
        cache = pathlib.Path(remap_result["_nexus_cache"])
        file_tree = json.loads((cache / "04_file_tree.json").read_text())
        paths = {f["path"] for f in file_tree["files"]}

        manifest_json = json.loads(
            (pathlib.Path(__file__).parent.parent / "golden_paths" / "nextjs-static" / "manifest.json").read_text()
        )
        required = manifest_json["requiredFiles"]
        missing = [r for r in required if r not in paths]
        assert missing == [], f"Required files missing from file tree after remap: {missing}"

    @pytest.mark.asyncio
    async def test_validate_has_no_missing_required_errors(self, tmp_path):
        """validate_output must not return MISSING_REQUIRED errors after our reference fix."""
        # Minimal portfolio-like source
        (tmp_path / "Hero.tsx").write_text(
            "export function Hero() { return <section>Hero</section>; }"
        )
        (tmp_path / "Experience.tsx").write_text(
            "export function Experience() { return <section>Experience</section>; }"
        )
        manifest = await self.codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static", project_name="e2e-noerror"
        )
        remap_result = json.loads(await self.remap(manifest))
        validate_result = json.loads(
            await self.validate(json.dumps({
                "project_name": "e2e-noerror",
                "golden_path": "nextjs-static",
                "_nexus_cache": remap_result["_nexus_cache"],
            }))
        )
        missing_required_errors = [
            e for e in validate_result.get("errors", [])
            if e.startswith("MISSING_REQUIRED")
        ]
        assert missing_required_errors == [], (
            f"validate_output still has MISSING_REQUIRED errors:\n"
            + "\n".join(missing_required_errors)
        )

    @pytest.mark.asyncio
    async def test_experience_routes_to_sections_not_ui(self, tmp_path):
        """Experience, Projects, Skills should land in components/sections/, not components/ui/."""
        for name in ["Experience", "Projects", "Skills"]:
            (tmp_path / f"{name}.tsx").write_text(
                f"export function {name}() {{ return <section>{name}</section>; }}"
            )
        manifest = await self.codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static", project_name="e2e-sections"
        )
        remap_result = json.loads(await self.remap(manifest))
        cache = pathlib.Path(remap_result["_nexus_cache"])
        file_tree = json.loads((cache / "04_file_tree.json").read_text())
        paths = [f["path"] for f in file_tree["files"]]

        for name in ["Experience", "Projects", "Skills"]:
            in_sections = any(f"components/sections/{name}.tsx" == p for p in paths)
            in_ui = any(f"components/ui/{name}.tsx" == p for p in paths)
            assert in_sections, f"{name} not found in components/sections/ — paths: {paths}"
            assert not in_ui, f"{name} incorrectly placed in components/ui/"

    @pytest.mark.asyncio
    async def test_shadcn_passthrough_no_broken_import_cascade(self, tmp_path):
        """
        When a shadcn file is auto-passthrough'd, its @/lib/utils import must resolve
        (because lib/utils.ts is now seeded from reference).
        No BROKEN_IMPORT errors should appear.
        """
        (tmp_path / "button.tsx").write_text(
            '"use client";\n'
            'import { cn } from "@/lib/utils";\n'
            'import { Slot } from "@radix-ui/react-slot";\n'
            'export function Button({ className, ...props }) {\n'
            '  return <Slot className={cn("btn", className)} {...props} />;\n'
            '}\n'
        )
        manifest = await self.codebase_ingest(
            project_dir=str(tmp_path), golden_path="nextjs-static", project_name="e2e-broken-import"
        )
        remap_result = json.loads(await self.remap(manifest))
        validate_result = json.loads(
            await self.validate(json.dumps({
                "project_name": "e2e-broken-import",
                "golden_path": "nextjs-static",
                "_nexus_cache": remap_result["_nexus_cache"],
            }))
        )
        broken_import_errors = [
            e for e in validate_result.get("errors", [])
            if e.startswith("BROKEN_IMPORT")
        ]
        assert broken_import_errors == [], (
            f"BROKEN_IMPORT errors found (lib/utils.ts not seeded?):\n"
            + "\n".join(broken_import_errors)
        )
