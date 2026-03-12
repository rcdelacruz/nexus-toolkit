"""
validate_output — static analysis of the generated file tree.

Runs after remap_to_golden_path + LLM transformation, before package_output.
Returns structured errors and warnings so the LLM can fix issues.

Checks:
  1.  Missing requiredFiles from manifest.json
  2.  Broken @/ imports — referenced but not in the file tree
  3.  Leftover Figma artifacts (inline styles, React.FC, bare React import)
  4.  Missing "use client" on components that use hooks / event handlers
  5.  Default exports in components/ (should be named exports)
  6.  oklch() usage (should be hsl())
  7.  tailwind.config reference (disallowed in Tailwind v4)
  8.  Hardcoded hex colors outside CSS files
  9.  Missing globals.css
  10. process.env.* in vite-spa (should be import.meta.env.VITE_*)
  11. Orphan files — seeded by reference boilerplate but never imported (unreachable)
  12. Unprocessed queue files — 05_queue/ still has items (transformation incomplete)
  13. Unconverted Vite/relative imports in Next.js output (raw Figma source not converted)
  14. Duplicate paths in file tree (agent appended instead of updating)
  15. Unsafe browser globals (localStorage/sessionStorage without SSR guard)
  16. Debug console statements in production code
  17. Missing error boundary files (error.tsx, not-found.tsx)
  18. Missing env.ts (Zod env validation)
  19. Missing logger.ts (pino structured logger for server paths)
  20. console.* in server-side code (should use pino logger)
  21. Missing audit columns in Prisma schema (deletedAt, createdById)
  22. Missing health endpoint (/api/health route for Docker healthchecks)
  23. Missing instrumentation.ts (SIGTERM/SIGINT graceful shutdown)
  24. Missing CSRF origin validation helper (lib/csrf.ts)
  25. Missing HTML sanitize helper (lib/sanitize.ts, isomorphic-dompurify)
  26. Unresolved __PROJECT_DESCRIPTION__ placeholder in README.md
"""

import json
import logging
import pathlib
import re

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

NEXUS_ROOT = pathlib.Path(__file__).parent.parent.parent
GOLDEN_PATHS_DIR = NEXUS_ROOT / "golden_paths"

# ── Regex helpers ──────────────────────────────────────────────────────────────

# Matches any @/foo/bar import path
_AT_IMPORT_RE = re.compile(r'from\s+["\'](@/[^"\']+)["\']')

# Figma artifact: inline style prop
_INLINE_STYLE_RE = re.compile(r'\bstyle=\{\{')

# Intentional runtime inline styles — not Figma artifacts:
#   Radix UI progress bar:  style={{ transform: `translateX(-${...}%)` }}
#   Recharts / chart.tsx:   style={{ '--color-foo': '...' }}  (CSS custom property injection)
#   Dynamic theming:        style={{ backgroundColor: someColorProp }}
_ALLOWED_INLINE_STYLE_RE = re.compile(
    r'style=\{\{\s*transform\s*:'          # Radix translateX animation
    r'|style=\{\{\s*["\']--[\w-]+'         # CSS custom property injection (Recharts)
    r'|style=\{\{\s*backgroundColor\s*:\s*\w+\s*\}\}'  # prop-driven dynamic color
)

# Figma artifact: React.FC / React.FunctionComponent type annotation
_REACT_FC_RE = re.compile(r':\s*React\.(FC|FunctionComponent)\b')

# Figma artifact: bare React default import
_BARE_REACT_IMPORT_RE = re.compile(r'^import React from ["\']react["\']', re.MULTILINE)

# Hooks / events that need "use client"
_CLIENT_HOOKS_RE = re.compile(
    r'\b(useState|useEffect|useRef|useCallback|useMemo|useReducer|useContext'
    r'|useLayoutEffect|useTransition|useDeferredValue|useId|useSyncExternalStore)\b'
)
_CLIENT_EVENTS_RE = re.compile(r'\bon[A-Z]\w+\s*=\s*\{')

# Default export in a component file
_DEFAULT_EXPORT_RE = re.compile(r'\bexport\s+default\s+function\b')

# oklch() color usage
_OKLCH_RE = re.compile(r'\boklch\(')

# tailwind.config reference
_TAILWIND_CONFIG_RE = re.compile(r'tailwind\.config\b')

# Hardcoded hex colors (not in a CSS file)
_HEX_COLOR_RE = re.compile(r'(?<!["\w])#[0-9A-Fa-f]{6}\b')

# process.env usage
_PROCESS_ENV_RE = re.compile(r'\bprocess\.env\b')

# Relative imports that should have been converted to @/ aliases
_RELATIVE_IMPORT_RE = re.compile(r'from\s+["\'](\./|\.\./)([^"\']+)["\']')

# Vite-specific patterns that must not appear in Next.js outputs
_VITE_PATTERN_RE = re.compile(r'from\s+["\']react-router-dom["\']|createBrowserRouter|RouterProvider')

# Browser-only globals that crash on SSR if accessed outside a typeof window guard
_BROWSER_GLOBALS_RE = re.compile(r'\b(localStorage|sessionStorage)\b')
_SSR_GUARD_RE = re.compile(r'typeof\s+window\s*!==?\s*["\']undefined["\']|typeof\s+window\s*===?\s*["\']undefined["\']')

# Debug console statements
_CONSOLE_LOG_RE = re.compile(r'\bconsole\.(log|warn|error|debug|info)\s*\(')

# All import paths (both @/ and relative) — used for reachability graph
_ALL_IMPORT_RE = re.compile(r'from\s+["\'](@/[^"\']+|\.\.?/[^"\']+)["\']')

# File extensions that are always valid without being imported (config / meta files)
_CONFIG_EXTENSIONS = {".json", ".md", ".gitignore", ".env", ".lock", ".yaml", ".yml", ".toml",
                      ".dart",    # Dart/Flutter files are never imported by TypeScript
                      ".prisma",  # Prisma schema
                      ".sql",     # SQL migration/seed files
                      ".conf",    # nginx.conf and similar server configs
                      }
_CONFIG_PREFIXES = (
    "public/",          # Static assets
    "apps/mobile/",     # Flutter/RN mobile app (not imported by web TS)
    ".husky/",          # Git hooks
    "packages/",        # Monorepo workspace packages (compiled separately, not via @/ imports)
    "tests/",           # Test infrastructure (setup, MSW handlers) — not imported by app code
    "apps/web/tests/",  # Monorepo test infrastructure
)
_CONFIG_STEMS = {
    "package", "tsconfig", "next.config", "postcss.config", "tailwind.config",
    ".gitignore", ".eslintrc", ".prettierrc", "readme", "license",
    # Common tooling files that are never imported
    "dockerfile", "makefile", ".env", ".editorconfig",
    # Any file whose stem ends in .config (eslint.config, commitlint.config, etc.)
    ".config",
    # Next.js files loaded by the framework, never via import statement
    "proxy", "instrumentation",
    # Phase 1/2 utility files — standalone helpers, not pre-wired in boilerplate imports
    "env", "logger", "csrf", "sanitize",
    # Package manager config
    ".npmrc",
    # nginx server config
    "nginx",
    # Database seed — run standalone via tsx, not imported by app
    "seed",
}


def _is_config_file(path: str) -> bool:
    """Return True for files that are valid without being imported by anything."""
    p = pathlib.PurePosixPath(path)
    if p.suffix.lower() in _CONFIG_EXTENSIONS:
        return True
    # TypeScript declaration files (.d.ts) are always infrastructure
    if path.endswith(".d.ts"):
        return True
    if any(path.startswith(prefix) for prefix in _CONFIG_PREFIXES):
        return True
    stem_lower = p.stem.lower()
    if any(cs in stem_lower or stem_lower == cs for cs in _CONFIG_STEMS):
        return True
    return False


def _resolve_import(import_path: str, importer_path: str, all_paths: set[str]) -> str | None:
    """
    Resolve an import path to a file tree path.
    Handles both @/ absolute aliases and relative imports.
    Returns the matching tree path or None.
    """
    if import_path.startswith("@/"):
        candidates = _path_to_fs(import_path)
    else:
        # Relative import — resolve from the importer's directory
        importer_dir = pathlib.PurePosixPath(importer_path).parent
        resolved = (importer_dir / import_path).as_posix()
        # Normalise (remove ../ hops that PurePosixPath already handled)
        tail = resolved.lstrip("./")
        candidates = [
            tail,
            tail + ".ts",
            tail + ".tsx",
            tail + ".js",
            tail + ".jsx",
            tail + "/index.ts",
            tail + "/index.tsx",
        ]
    for c in candidates:
        if c in all_paths:
            return c
    return None


def _build_reachability(files: list[dict]) -> set[str]:
    """
    Walk the import graph from all entry-point files and return the set of
    reachable file paths.

    Entry points:
      - app/**/page.tsx, app/**/layout.tsx  (Next.js App Router)
      - src/app/**/page.tsx, src/app/**/layout.tsx
      - app/globals.css (always reachable — imported by layout)
      - index.html, src/main.tsx, src/App.tsx  (Vite SPA)
    """
    all_paths: set[str] = {f["path"] for f in files}
    content_map: dict[str, str] = {f["path"]: f.get("content", "") for f in files}

    # Identify entry points
    roots: set[str] = set()
    for path in all_paths:
        p = pathlib.PurePosixPath(path)
        parts = p.parts
        # Next.js App Router entries
        if p.name in ("page.tsx", "layout.tsx", "page.ts", "layout.ts"):
            if "app" in parts:
                roots.add(path)
        # Vite SPA entries
        if p.name in ("main.tsx", "main.ts", "App.tsx", "App.ts", "index.html"):
            roots.add(path)
        # CSS globals are always reachable (layout imports them)
        if p.suffix == ".css":
            roots.add(path)

    # BFS through the import graph
    reachable: set[str] = set(roots)
    queue = list(roots)
    while queue:
        current = queue.pop()
        content = content_map.get(current, "")
        for match in _ALL_IMPORT_RE.finditer(content):
            imp = match.group(1)
            resolved = _resolve_import(imp, current, all_paths)
            if resolved and resolved not in reachable:
                reachable.add(resolved)
                queue.append(resolved)

    return reachable


def _path_to_fs(import_path: str) -> list[str]:
    """
    Convert @/foo/bar to the candidate file tree paths that would satisfy it.
    Returns a list of candidates (with and without extension, index.ts, etc.)
    """
    tail = import_path[len("@/"):]  # e.g. "components/ui/Button"
    candidates = [
        tail,
        tail + ".ts",
        tail + ".tsx",
        tail + ".js",
        tail + ".jsx",
        tail + "/index.ts",
        tail + "/index.tsx",
    ]
    # For t3-stack the @/* alias maps to src/*, so also try src/ prefix
    return candidates + ["src/" + c for c in candidates]


def _is_client_component(content: str) -> bool:
    return '"use client"' in content or "'use client'" in content


def _needs_use_client(content: str) -> bool:
    return bool(_CLIENT_HOOKS_RE.search(content) or _CLIENT_EVENTS_RE.search(content))


def _load_manifest(golden_path: str) -> dict:
    p = GOLDEN_PATHS_DIR / golden_path / "manifest.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _run_checks(
    files: list[dict],
    golden_path: str,
    cache_dir: pathlib.Path | None = None,
    passthrough_paths: set[str] | None = None,
    reference_paths: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    # Build a set of all paths present in the file tree
    all_paths: set[str] = {f["path"] for f in files}

    manifest = _load_manifest(golden_path)
    required_files: list[str] = manifest.get("requiredFiles", [])
    globals_css = manifest.get("tailwind", {}).get("cssFile", "app/globals.css")

    # ── Check 11: Unprocessed queue files (transformation incomplete) ─────────
    # Parse the output path from each remaining queue file (line: **Output path:** `...`).
    # If the path is already in the file tree with non-empty content, the agent wrote
    # the transform but forgot to delete the queue file → warning only.
    # If the path is absent or empty → the file was never transformed → hard error.
    _OUTPUT_PATH_RE = re.compile(r'\*\*Output path:\*\*\s*`([^`]+)`')
    if cache_dir is not None:
        queue_dir = cache_dir / "05_queue"
        if queue_dir.exists():
            remaining = sorted(queue_dir.iterdir())
            if remaining:
                content_map = {f["path"]: f.get("content", "") for f in files}
                truly_missing = []
                stale_only = []
                for qf in remaining:
                    try:
                        text = qf.read_text(encoding="utf-8")
                        m = _OUTPUT_PATH_RE.search(text)
                        out_path = m.group(1) if m else None
                    except Exception:
                        out_path = None
                    if out_path and content_map.get(out_path, "").strip():
                        stale_only.append(qf.name)
                    else:
                        truly_missing.append(qf.name)
                if truly_missing:
                    errors.append(
                        f"INCOMPLETE_QUEUE: {len(truly_missing)} queue file(s) were never transformed: "
                        f"{', '.join(truly_missing[:5])}"
                        + ("..." if len(truly_missing) > 5 else "")
                    )
                if stale_only:
                    warnings.append(
                        f"STALE_QUEUE_FILE: {len(stale_only)} queue file(s) were transformed but not deleted: "
                        f"{', '.join(stale_only[:5])}"
                        + ("..." if len(stale_only) > 5 else "")
                        + " — delete them to clean up"
                    )

    # ── Check 12: Duplicate paths in file tree ────────────────────────────────
    seen_once: set[str] = set()
    for f in files:
        p = f["path"]
        if p in seen_once:
            errors.append(
                f"DUPLICATE_PATH: '{p}' appears more than once in the file tree — "
                f"agent appended instead of updating; only the last entry will be packaged"
            )
        seen_once.add(p)

    # ── Check 13: Orphan files (reachability graph) ───────────────────────────
    if passthrough_paths is None:
        passthrough_paths = set()
    if reference_paths is None:
        reference_paths = set()
    reachable = _build_reachability(files)
    for f in files:
        path = f["path"]
        if path not in reachable and not _is_config_file(path):
            if path in passthrough_paths:
                # shadcn/ui primitives are included for future use — not a real orphan
                warnings.append(
                    f"SHADCN_PASSTHROUGH: '{path}' is a shadcn/ui primitive included for "
                    f"future use but not imported by this project — safe to ignore"
                )
            elif path in reference_paths:
                # Golden path reference boilerplate — seeded as starter stubs.
                # Not imported by this design, will be stripped from the final ZIP.
                pass
            else:
                warnings.append(
                    f"ORPHAN_FILE: '{path}' is never imported by any reachable file — "
                    f"will be stripped from the final ZIP; remove it from the Figma source "
                    f"or add an import to keep it"
                )

    # ── Check 1: Missing required files ───────────────────────────────────────
    for req in required_files:
        if req not in all_paths:
            errors.append(
                f"MISSING_REQUIRED: '{req}' listed in manifest.requiredFiles but not in file tree — "
                f"add it to golden_paths/{golden_path}/reference/ so it is seeded automatically, "
                f"or generate it during transformation"
            )

    # ── Check 2: globals.css present ──────────────────────────────────────────
    if globals_css not in all_paths:
        errors.append(f"MISSING_GLOBALS_CSS: '{globals_css}' not found in file tree")

    # ── Check 2b: PascalCase shadcn primitive filenames in components/ui/ ────
    # e.g. Button.tsx conflicts with button.tsx on case-insensitive filesystems
    # and triggers TypeScript forceConsistentCasingInFileNames errors
    for p in all_paths:
        parts = p.split("/")
        if "ui" in parts:
            ui_idx = parts.index("ui")
            if ui_idx == len(parts) - 2:  # file is directly inside a ui/ dir
                fname = parts[-1]
                stem = pathlib.PurePosixPath(fname).stem
                if stem and stem[0].isupper():
                    errors.append(
                        f"PASCALCASE_UI_FILE: '{p}' — shadcn/ui primitives must use "
                        f"lowercase filenames (e.g. '{p.replace(fname, fname[0].lower() + fname[1:])}')"
                    )

    for file_entry in files:
        path: str = file_entry["path"]
        content: str = file_entry.get("content", "")

        # Skip binary placeholders and non-code files
        if content == "# binary asset placeholder":
            continue
        ext = pathlib.PurePosixPath(path).suffix.lower()
        is_tsx = ext in (".tsx", ".ts", ".jsx", ".js")
        is_css = ext == ".css"

        if not is_tsx:
            continue  # Only analyse TypeScript/JSX files

        # ── Check 3: Broken @/ imports ─────────────────────────────────────
        for match in _AT_IMPORT_RE.finditer(content):
            imp = match.group(1)
            candidates = _path_to_fs(imp)
            if not any(c in all_paths for c in candidates):
                errors.append(f"BROKEN_IMPORT: '{path}' imports '{imp}' but that path is not in the file tree")

        # ── Check 4: Leftover Figma artifacts ─────────────────────────────
        # Suppress inline-style warnings for:
        #   a) shadcn/ui passthrough files (auto-cleaned, no LLM transform)
        #   b) files where every inline style matches a known library pattern
        #      (Radix UI translateX animation, Recharts CSS custom property
        #      injection, prop-driven dynamic backgroundColor)
        if _INLINE_STYLE_RE.search(content) and path not in passthrough_paths:
            all_styles = _INLINE_STYLE_RE.findall(content)
            allowed_styles = _ALLOWED_INLINE_STYLE_RE.findall(content)
            if len(all_styles) != len(allowed_styles):
                warnings.append(f"FIGMA_ARTIFACT: '{path}' still has inline style={{{{...}}}} — convert to Tailwind classes")

        if _REACT_FC_RE.search(content):
            warnings.append(f"FIGMA_ARTIFACT: '{path}' uses React.FC type annotation — remove it (React 19)")

        if _BARE_REACT_IMPORT_RE.search(content):
            warnings.append(f"FIGMA_ARTIFACT: '{path}' has bare 'import React from \"react\"' — not needed in React 19")

        # ── Check 5: Missing "use client" ──────────────────────────────────
        # Only relevant for Next.js golden paths — vite-spa is client-only, no
        # server components exist, so every component can freely use hooks.
        # React Native / Expo files (apps/mobile/, packages/ui-mobile/) do not
        # use "use client" — skip them entirely.
        _is_native_file = path.startswith("apps/mobile/") or path.startswith("packages/ui-mobile/")
        if golden_path != "vite-spa" and not _is_native_file:
            if _needs_use_client(content) and not _is_client_component(content):
                # server pages with async server actions are OK — they use "use server" inside
                if '"use server"' not in content and "'use server'" not in content:
                    errors.append(f"MISSING_USE_CLIENT: '{path}' uses hooks or event handlers but has no \"use client\" directive")

        # ── Check 6: Default export in components/ ─────────────────────────
        if path.startswith("components/") or path.startswith("src/components/"):
            if _DEFAULT_EXPORT_RE.search(content):
                warnings.append(f"DEFAULT_EXPORT: '{path}' uses 'export default function' — prefer named export")

        # ── Check 7: oklch() usage ─────────────────────────────────────────
        if _OKLCH_RE.search(content):
            warnings.append(f"OKLCH_COLOR: '{path}' uses oklch() — convert to hsl() per token-extraction rules")

        # ── Check 8: tailwind.config reference ────────────────────────────
        if _TAILWIND_CONFIG_RE.search(content):
            warnings.append(f"TAILWIND_CONFIG: '{path}' references tailwind.config — Tailwind v4 is CSS-first, remove this")

        # ── Check 9: Hardcoded hex colors in TSX ──────────────────────────
        if _HEX_COLOR_RE.search(content):
            # Count them to keep the message concise
            hits = _HEX_COLOR_RE.findall(content)
            warnings.append(
                f"HARDCODED_HEX: '{path}' has {len(hits)} hardcoded hex color(s) ({', '.join(hits[:3])}{'...' if len(hits) > 3 else ''}) — use CSS var tokens"
            )

        # ── Check 10: process.env in vite-spa ─────────────────────────────
        if golden_path == "vite-spa" and _PROCESS_ENV_RE.search(content):
            errors.append(f"PROCESS_ENV: '{path}' uses process.env — use import.meta.env.VITE_* in Vite SPA")

        # ── Check 11 (per-file): Layout stub detection ─────────────────────
        if path.startswith("components/layout/"):
            line_count = len([l for l in content.splitlines() if l.strip()])
            if line_count < 15:
                warnings.append(
                    f"LAYOUT_STUB: '{path}' has only {line_count} non-empty lines — "
                    f"may be a reference placeholder rather than the actual Figma component"
                )

        # ── Check 15: Unsafe browser globals (SSR crash) ──────────────────
        if _BROWSER_GLOBALS_RE.search(content) and not _SSR_GUARD_RE.search(content):
            errors.append(
                f"UNSAFE_BROWSER_GLOBALS: '{path}' accesses localStorage/sessionStorage "
                f"without a 'typeof window !== \"undefined\"' guard — will crash during SSR. "
                f"Use: typeof window !== 'undefined' ? localStorage.getItem(key) : null, "
                f"or move access inside useEffect()"
            )

        # ── Check 16: Debug console statements ────────────────────────────
        # Exempt intentional server-side console use in lifecycle/infra files
        _console_exempt = (
            path.endswith("instrumentation.ts")
            or path.endswith("seed.ts")
            or path.startswith("tests/")
            or path.startswith("apps/web/tests/")
        )
        if not _console_exempt and _CONSOLE_LOG_RE.search(content):
            warnings.append(
                f"CONSOLE_LOG: '{path}' contains console.log/warn/error — remove before shipping"
            )

        # ── Check 14: Unconverted Vite/relative imports in Next.js output ──
        # Exempt generated/ stubs (Prisma-generated, use relative imports by design)
        # and test files (relative imports within tests/ are conventional)
        _import_exempt = (
            path.startswith("generated/")
            or path.startswith("apps/web/generated/")
            or path.startswith("src/generated/")
            or path.startswith("tests/")
            or path.startswith("apps/web/tests/")
            or path.endswith(".test.ts")
            or path.endswith(".test.tsx")
            or path.endswith(".spec.ts")
            or path.endswith(".spec.tsx")
        )
        if golden_path not in ("vite-spa",) and not _import_exempt:
            # Relative imports that should be @/ aliases
            for match in _RELATIVE_IMPORT_RE.finditer(content):
                rel = match.group(0)
                warnings.append(
                    f"UNCONVERTED_IMPORT: '{path}' still has relative import `{rel.strip()}` — "
                    f"convert to @/ alias (raw Figma source may not have been transformed)"
                )
            # react-router-dom usage in Next.js output
            if _VITE_PATTERN_RE.search(content):
                errors.append(
                    f"VITE_ARTIFACT: '{path}' uses react-router-dom or Vite router patterns — "
                    f"these are invalid in {golden_path}; use Next.js App Router instead"
                )

    # ── Check 17: Missing error boundary files ────────────────────────────────
    # For Next.js golden paths: error.tsx and not-found.tsx should be present
    _NEXTJS_PATHS = {"nextjs-fullstack", "nextjs-static", "t3-stack", "monorepo",
                     "full-stack-rn", "full-stack-flutter"}
    if golden_path in _NEXTJS_PATHS:
        # Determine the app root based on golden path conventions
        if golden_path == "t3-stack":
            app_roots = ["src/app/"]
        elif golden_path in {"monorepo", "full-stack-rn", "full-stack-flutter"}:
            app_roots = ["apps/web/app/"]
        else:
            app_roots = ["app/"]

        for app_root in app_roots:
            if not any(p.startswith(app_root + "error") for p in all_paths):
                warnings.append(
                    f"MISSING_ERROR_BOUNDARY: no '{app_root}error.tsx' found — "
                    f"add an error boundary for graceful error recovery"
                )
            if not any(p.startswith(app_root + "not-found") for p in all_paths):
                warnings.append(
                    f"MISSING_NOT_FOUND: no '{app_root}not-found.tsx' found — "
                    f"add a 404 page"
                )

    # ── Check 18: Missing env.ts ───────────────────────────────────────────────
    _ENV_TS_PATHS = {
        "nextjs-fullstack": ["lib/env.ts"],
        "t3-stack": ["src/lib/env.ts"],
        "monorepo": ["apps/web/lib/env.ts"],
        "full-stack-rn": ["apps/web/lib/env.ts"],
        "full-stack-flutter": ["apps/web/lib/env.ts"],
        "nextjs-static": ["lib/env.ts"],
        "vite-spa": ["src/lib/env.ts"],
    }
    expected_env = _ENV_TS_PATHS.get(golden_path, [])
    for env_path in expected_env:
        if env_path not in all_paths:
            warnings.append(
                f"MISSING_ENV_VALIDATION: '{env_path}' not found — "
                f"add Zod-based env validation to catch missing env vars at startup"
            )

    # ── Check 19: Missing logger.ts (server paths only) ───────────────────────
    _LOGGER_TS_PATHS = {
        "nextjs-fullstack": "lib/logger.ts",
        "t3-stack": "src/lib/logger.ts",
        "monorepo": "apps/web/lib/logger.ts",
        "full-stack-rn": "apps/web/lib/logger.ts",
        "full-stack-flutter": "apps/web/lib/logger.ts",
    }
    expected_logger = _LOGGER_TS_PATHS.get(golden_path)
    if expected_logger and expected_logger not in all_paths:
        warnings.append(
            f"MISSING_LOGGER: '{expected_logger}' not found — "
            f"add a pino structured logger for production-grade observability"
        )

    # ── Check 20: console.* in server-side code ───────────────────────────────
    # For server-only files (not "use client"), warn that console.* should use logger
    _SERVER_PATHS = {"nextjs-fullstack", "t3-stack", "monorepo", "full-stack-rn", "full-stack-flutter"}
    if golden_path in _SERVER_PATHS:
        for file_entry in files:
            path = file_entry["path"]
            content = file_entry.get("content", "")
            if content == "# binary asset placeholder":
                continue
            ext = pathlib.PurePosixPath(path).suffix.lower()
            if ext not in (".ts", ".tsx"):
                continue
            # Only check files that look like server-side code (API routes, server actions, tRPC)
            is_server_file = (
                "/api/" in path
                or "server/" in path
                or path.endswith("/route.ts")
                or path.endswith("/actions.ts")
                or path.endswith("trpc.ts")
            )
            if is_server_file and not _is_client_component(content) and _CONSOLE_LOG_RE.search(content):
                warnings.append(
                    f"SERVER_CONSOLE: '{path}' uses console.* in server code — "
                    f"use the pino logger from lib/logger.ts (or apps/web/lib/logger.ts) instead"
                )

    # ── Check 21: Missing audit columns in Prisma schema ──────────────────────
    # For Prisma-based golden paths, the schema should have deletedAt + audit trail on domain models
    _PRISMA_PATHS = {
        "nextjs-fullstack": "prisma/schema.prisma",
        "t3-stack": "prisma/schema.prisma",
        "monorepo": "packages/db/prisma/schema.prisma",
    }
    prisma_schema_path = _PRISMA_PATHS.get(golden_path)
    if prisma_schema_path:
        schema_entry = next(
            (f for f in files if f["path"] == prisma_schema_path), None
        )
        if schema_entry:
            schema_content = schema_entry.get("content", "")
            if "deletedAt" not in schema_content:
                warnings.append(
                    f"MISSING_AUDIT_COLUMNS: '{prisma_schema_path}' has no 'deletedAt' field — "
                    f"add deletedAt DateTime? to domain models for soft-delete support"
                )
            if "createdById" not in schema_content:
                warnings.append(
                    f"MISSING_AUDIT_COLUMNS: '{prisma_schema_path}' has no 'createdById' field — "
                    f"add createdById/updatedById audit trail fields to domain models"
                )

    # ── Check 22: Missing health endpoint (server paths only) ─────────────────
    _HEALTH_PATHS = {
        "nextjs-fullstack": "app/api/health/route.ts",
        "t3-stack": "src/app/api/health/route.ts",
        "monorepo": "apps/web/app/api/health/route.ts",
        "full-stack-rn": "apps/web/app/api/health/route.ts",
        "full-stack-flutter": "apps/web/app/api/health/route.ts",
    }
    expected_health = _HEALTH_PATHS.get(golden_path)
    if expected_health and expected_health not in all_paths:
        warnings.append(
            f"MISSING_HEALTH_ENDPOINT: '{expected_health}' not found — "
            f"add a /api/health GET route returning {{status:'ok', timestamp, uptime}} for Docker healthchecks"
        )

    # ── Check 23: Missing instrumentation.ts (server paths only) ──────────────
    _INSTRUMENTATION_PATHS = {
        "nextjs-fullstack": "instrumentation.ts",
        "t3-stack": "src/instrumentation.ts",
        "monorepo": "apps/web/instrumentation.ts",
        "full-stack-rn": "apps/web/instrumentation.ts",
        "full-stack-flutter": "apps/web/instrumentation.ts",
    }
    expected_instrumentation = _INSTRUMENTATION_PATHS.get(golden_path)
    if expected_instrumentation and expected_instrumentation not in all_paths:
        warnings.append(
            f"MISSING_INSTRUMENTATION: '{expected_instrumentation}' not found — "
            f"add instrumentation.ts to register SIGTERM/SIGINT graceful shutdown handlers"
        )

    # ── Check 24: Missing CSRF helper (server paths only) ─────────────────────
    _CSRF_TS_PATHS = {
        "nextjs-fullstack": "lib/csrf.ts",
        "t3-stack": "src/lib/csrf.ts",
        "monorepo": "apps/web/lib/csrf.ts",
        "full-stack-rn": "apps/web/lib/csrf.ts",
        "full-stack-flutter": "apps/web/lib/csrf.ts",
    }
    expected_csrf = _CSRF_TS_PATHS.get(golden_path)
    if expected_csrf and expected_csrf not in all_paths:
        warnings.append(
            f"MISSING_CSRF: '{expected_csrf}' not found — "
            f"add CSRF origin validation for API route handlers"
        )

    # ── Check 25: Missing sanitize helper (server paths only) ─────────────────
    _SANITIZE_TS_PATHS = {
        "nextjs-fullstack": "lib/sanitize.ts",
        "t3-stack": "src/lib/sanitize.ts",
        "monorepo": "apps/web/lib/sanitize.ts",
        "full-stack-rn": "apps/web/lib/sanitize.ts",
        "full-stack-flutter": "apps/web/lib/sanitize.ts",
    }
    expected_sanitize = _SANITIZE_TS_PATHS.get(golden_path)
    if expected_sanitize and expected_sanitize not in all_paths:
        warnings.append(
            f"MISSING_SANITIZE: '{expected_sanitize}' not found — "
            f"add isomorphic-dompurify sanitize helper for user-generated HTML"
        )

    # ── Check 26: Unresolved __PROJECT_DESCRIPTION__ in README ────────────────
    readme_entry = next((f for f in files if f["path"] in ("README.md", "apps/web/README.md")), None)
    if readme_entry and "__PROJECT_DESCRIPTION__" in readme_entry.get("content", ""):
        warnings.append(
            "UNRESOLVED_PLACEHOLDER: README.md still contains '__PROJECT_DESCRIPTION__' — "
            "replace it with 1-2 sentences describing what this project does"
        )

    return errors, warnings


def register_validate_tool(mcp: FastMCP) -> None:

    @mcp.tool()
    async def validate_output(file_tree_json: str) -> str:
        """
        Validate the generated file tree for code correctness and production readiness.

        Run this AFTER the LLM has transformed files_to_transform and updated
        04_file_tree.json, and BEFORE calling package_output.

        Checks performed:
        - Missing required files (per manifest.requiredFiles)
        - Broken @/ imports (path not present in file tree)
        - Leftover Figma artifacts (inline styles, React.FC, bare React import)
        - Missing "use client" on components that use hooks/events
        - Default exports in components/ (must be named exports)
        - oklch() color usage (must be hsl())
        - tailwind.config references (disallowed in Tailwind v4)
        - Hardcoded hex colors in TSX files
        - process.env in vite-spa (must be import.meta.env.VITE_*)

        Args:
            file_tree_json: The small summary JSON returned by remap_to_golden_path
                            (contains _nexus_cache pointer). The tool reads the full
                            04_file_tree.json from disk.

        Returns:
            JSON with:
            {
              "passed": bool,
              "error_count": int,
              "warning_count": int,
              "errors": ["BROKEN_IMPORT: ...", ...],
              "warnings": ["FIGMA_ARTIFACT: ...", ...],
              "review_prompt": "<contents of prompts/review.md>",
              "instructions": "Fix all errors before calling package_output. ..."
            }

            "passed" is true only when error_count == 0.
            Warnings are informational — package_output can still be called, but
            the LLM should try to fix warnings too for production quality.
        """
        logger.info("validate_output called")

        try:
            summary = json.loads(file_tree_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}"})

        # Load the full file tree from disk cache
        cache = summary.get("_nexus_cache")
        if cache:
            cache_path = pathlib.Path(cache, "04_file_tree.json")
            try:
                file_tree = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception as e:
                return json.dumps({"error": f"Failed to read 04_file_tree.json: {str(e)}"})
        else:
            file_tree = summary  # fallback: summary is the file tree

        files = file_tree.get("files", [])
        if not files:
            return json.dumps({"error": "No files in file tree — run remap_to_golden_path first"})

        golden_path = file_tree.get("golden_path", summary.get("golden_path", "nextjs-fullstack"))
        project_name = file_tree.get("project_name", summary.get("project_name", "my-app"))
        cache_dir = pathlib.Path(cache) if cache else None
        passthrough_paths: set[str] = set(file_tree.get("passthrough_paths", []))
        reference_paths: set[str] = set(file_tree.get("reference_paths", []))

        errors, warnings = _run_checks(files, golden_path, cache_dir, passthrough_paths, reference_paths)
        passed = len(errors) == 0

        logger.info(
            f"validate_output complete — {len(errors)} errors, {len(warnings)} warnings, "
            f"passed={passed}, project={project_name}, golden_path={golden_path}"
        )

        instructions = (
            "All errors must be fixed before calling package_output. "
            "For each BROKEN_IMPORT error: ensure the imported component exists in the file tree "
            "or update the import path. "
            "For each MISSING_REQUIRED error: generate the missing file from the golden path templates. "
            "For each MISSING_USE_CLIENT error: add '\"use client\"' as the first line. "
            "Warnings should also be resolved for production-quality output — "
            "replace inline styles with Tailwind classes, hex colors with CSS var tokens, etc. "
            "After fixing, call validate_output again to confirm all errors are resolved, "
            "then call package_output."
        ) if not passed else (
            "All checks passed. Call package_output to create the downloadable ZIP."
        )

        return json.dumps({
            "passed": passed,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
            "instructions": instructions,
            "project_name": project_name,
            "golden_path": golden_path,
            "_nexus_cache": cache or "",
        })
