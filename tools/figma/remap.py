import datetime
import json
import logging
import pathlib
import re
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Root of the nexus-mcp repo (two levels up from tools/figma/)
NEXUS_ROOT = pathlib.Path(__file__).parent.parent.parent
GOLDEN_PATHS_DIR = NEXUS_ROOT / "golden_paths"

BINARY_PLACEHOLDER = "# binary asset placeholder"

# Stems that are framework/tooling artifacts — never Figma design files
DISCARD_STEMS = {
    # Build / framework config
    "main", "vite.config", "next.config", "tailwind.config",
    "postcss.config", "jest.config", "vitest.config",
    "drizzle.config", "prisma.config",
    # Linting / formatting / tooling
    "eslint.config", "commitlint.config", "prettier.config",
    "base", "next",  # eslint config stems
    # Backend / infrastructure stubs
    "db", "trpc", "server", "proxy", "query-client",
    "config", "react",
    # Barrel / utility stubs — reference boilerplate provides these
    "utils", "index",
    # Auth / middleware
    "auth", "middleware", "instrumentation",
    # App shell / routing stubs
    "root", "api", "route",
    # State management stubs
    "useAppStore",
}

ROOT_ENTRY_STEMS = {"app", "home", "homepage", "index", "landing", "root"}

# Import signals that mark a file as infrastructure, not a Figma design component
INFRA_IMPORT_SIGNALS = {
    "@prisma/client", "prisma/config",
    "@trpc/", "next-auth", "better-auth",
    "drizzle-orm", "@tanstack/react-query",
    "zustand", "@tanstack/react-router",
    "PrismaClient", "defineConfig",
}

ROUTE_MAP = {
    "home": "/", "index": "/", "landing": "/",
    "dashboard": "/dashboard", "admin": "/dashboard",
    "login": "/(auth)/login", "signin": "/(auth)/login",
    "signup": "/(auth)/signup", "register": "/(auth)/signup",
    "profile": "/profile", "settings": "/settings",
    "about": "/about", "contact": "/contact", "pricing": "/pricing",
}

SECTION_KEYWORDS = {
    # Common marketing/landing
    "section", "hero", "pricing", "testimonial", "cta", "faq",
    "banner", "about", "team", "contact", "blog", "features",
    # Portfolio & content-heavy sites
    "experience", "projects", "skills", "work", "portfolio",
    "gallery", "services", "clients", "stats", "metrics", "values",
    "awards", "timeline", "resume", "cv", "education", "certifications",
}

# ── Shadcn/ui passthrough ─────────────────────────────────────────────────────
# Components that import these packages are shadcn/ui primitives.
# They don't need LLM transformation — just ensure "use client" is present.
SHADCN_PASSTHROUGH_SIGNALS = (
    "@radix-ui/",
    "cmdk",
    "embla-carousel-react",
    "input-otp",
    "react-day-picker",
    "react-resizable-panels",
    "vaul",
    "recharts",
)



def _is_shadcn_primitive(content: str) -> bool:
    return any(sig in content for sig in SHADCN_PASSTHROUGH_SIGNALS)


def _clean_passthrough_imports(content: str) -> str:
    """
    Fix Figma-sourced shadcn imports so they resolve in a real Node project:

    1. Strip @version specifiers — Figma Make emits ``@radix-ui/react-slot@1.1.2``
       but Node only understands ``@radix-ui/react-slot``.
       A version pinned via ``@<digit>`` is stripped; scoped-package ``@org/`` prefixes
       (which start with a letter after ``@``) are left untouched.

    2. ``from "./utils"``   → ``from "@/lib/utils"``
    3. ``from "./button"``  → ``from "@/components/ui/button"``  (and any other
       bare relative sibling import like ``./dialog``, ``./label``, etc.)
    """
    # 1. Strip @version: only strip @<digit>... (not @org/ scoped prefixes)
    content = re.sub(r'@(\d[^"\']*)', '', content)

    # 2. Relative utils
    content = re.sub(r'from (["\'])\.\/utils\1', r'from \1@/lib/utils\1', content)

    # 3. Relative sibling UI components  (./button, ./dialog, ./label …)
    content = re.sub(
        r'from (["\'])\.\/([a-z][a-z0-9-]*)\1',
        r'from \1@/components/ui/\2\1',
        content,
    )
    return content


def _passthrough_shadcn(content: str) -> str:
    """Clean Figma-specific import issues and ensure 'use client' is present."""
    content = _clean_passthrough_imports(content)
    stripped = content.lstrip()
    if stripped.startswith('"use client"') or stripped.startswith("'use client'"):
        return content
    return '"use client";\n\n' + content


def _extract_versioned_packages(content: str) -> dict[str, str]:
    """
    Extract package → version from Figma Make's versioned import syntax.

    Figma Make pins exact versions inside the import specifier, e.g.:
        from "@radix-ui/react-slot@1.1.2"
        from "class-variance-authority@0.7.1"

    This reads those versions directly from the source — no hardcoded lookup
    table required.  The version is normalised to a caret range (``^x.y.z``)
    so npm/pnpm can apply compatible minor/patch updates.

    Only call this on the *raw* Figma content, before ``_clean_passthrough_imports``
    strips the version specifiers.
    """
    packages: dict[str, str] = {}
    pattern = re.compile(r'from\s+["\'](@?[^"\'./\s][^"\'@\s]*)@(\d[^"\']*)["\']')
    for match in pattern.finditer(content):
        pkg_name = match.group(1)
        raw_version = match.group(2).strip()
        packages[pkg_name] = f"^{raw_version}"
    return packages


def _inject_detected_packages(output_map: dict, detected: dict[str, str]) -> None:
    """
    Merge *detected* ``{package: version}`` entries into the output package.json.

    Only adds packages not already present in dependencies or devDependencies,
    preserving whatever the reference boilerplate already pins.
    """
    if not detected or "package.json" not in output_map:
        return
    try:
        pkg = json.loads(output_map["package.json"])
        deps = pkg.setdefault("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        added: list[str] = []
        for name, version in sorted(detected.items()):
            if name in deps or name in dev_deps:
                continue
            deps[name] = version
            added.append(f"{name}@{version}")
        if added:
            output_map["package.json"] = json.dumps(pkg, indent=2)
            logger.info(f"Auto-injected packages: {', '.join(added)}")
    except Exception as e:
        logger.warning(f"Failed to inject detected packages: {e}")


# ─────────────────────────────────────────────────────────────────────────────

def _load_input(json_str: str, cache_file: str) -> dict:
    """Load the full input data, preferring the disk cache when available."""
    data = json.loads(json_str)
    cache = data.get("_nexus_cache")
    if cache:
        full = pathlib.Path(cache, cache_file).read_text(encoding="utf-8")
        return json.loads(full)
    return data


def _load_golden_path_meta(golden_path: str) -> tuple[dict, dict]:
    """Load manifest.json; classification rules are embedded under manifest['classification']."""
    gp_dir = GOLDEN_PATHS_DIR / golden_path
    manifest = {}
    manifest_path = gp_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        logger.info(f"Loaded manifest for '{golden_path}'")
    else:
        logger.warning(f"No manifest.json found for golden path '{golden_path}'")
    rules = manifest.get("classification", {})
    return manifest, rules


def _load_reference_files(golden_path: str) -> list[dict]:
    """Read every file from the reference/ directory as working boilerplate."""
    ref_dir = GOLDEN_PATHS_DIR / golden_path / "reference"
    files = []
    if not ref_dir.exists():
        logger.warning(f"No reference/ directory for golden path '{golden_path}'")
        return files
    for fp in sorted(ref_dir.rglob("*")):
        if not fp.is_file():
            continue
        rel = fp.relative_to(ref_dir).as_posix()
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        files.append({"path": rel, "content": content})
    logger.info(f"Loaded {len(files)} reference files for '{golden_path}'")
    return files


def _is_infra_content(content: str) -> bool:
    """Return True if file imports infrastructure packages — not a Figma design component."""
    return any(signal in content for signal in INFRA_IMPORT_SIGNALS)


def _classify(stem: str, rules: dict, golden_path: str) -> str:
    """Classify a component stem into: root_page | discard | section | page | layout | feature | screen | widget | ui"""
    lower = stem.lower()
    if lower in ROOT_ENTRY_STEMS:
        return "root_page"
    if golden_path != "vite-spa" and lower in DISCARD_STEMS:
        return "discard"
    # Detect "Page" suffix BEFORE section keywords — stems like "AboutPage", "PricingPage",
    # "DashboardPage", "LoginPage" are pages, not sections, even if their core word appears
    # in SECTION_KEYWORDS (e.g. "about", "pricing", "contact").
    if lower.endswith("page") and len(lower) > 4:
        core = lower[:-4]  # "home" from "homepage", "about" from "aboutpage"
        if core in ("home", "index", "landing", "root", ""):
            return "root_page"
        return "page"
    # Check hardcoded section keywords first
    if any(kw in lower for kw in SECTION_KEYWORDS):
        return "section"
    categories = rules.get("categories", {})
    # Check manifest-defined signals. screen/widget are checked before feature so that
    # e.g. "LoginScreen" in a mobile golden path is not caught by a "Login" feature signal.
    for cat_name in ("page", "layout", "section", "screen", "widget", "feature", "ui"):
        cat = categories.get(cat_name, {})
        signals = [s.lower() for s in cat.get("signals", [])]
        for sig in signals:
            if sig in lower or lower == sig:
                return cat_name
    # If the manifest defines a "default" category, use it as fallback instead of "ui".
    # This lets golden paths redirect unrecognised components away from components/ui/.
    if "default" in categories:
        return "default"
    return "ui"


# Suffixes stripped from a component stem when deriving a clean domain / route slug.
# Ordered longest-first to avoid partial matches (e.g. "page" before "age").
# Covers mobile categories (screen/view/widget) and web feature/page categories.
_COMPONENT_SUFFIXES = (
    # mobile
    "screen", "view", "widget",
    # routing
    "page", "route",
    # feature components
    "form", "table", "list", "chart", "grid", "panel", "section", "card",
)


def _derive_domain(stem: str) -> str:
    """Strip a known component-type suffix from the stem and lowercase.

    e.g. LoginScreen → "login", DashboardTable → "dashboard", LoginForm → "login"
    Falls back to the full lowercased stem when no suffix matches.
    """
    lower = stem.lower()
    for suffix in _COMPONENT_SUFFIXES:
        if lower.endswith(suffix) and len(lower) > len(suffix):
            return lower[: -len(suffix)]
    return lower


def _resolve_output_path(stem: str, category: str, rules: dict) -> str:
    """Turn a (stem, category) pair into the correct output file path.

    Supported template placeholders:
      {ComponentName} — the stem as-is (PascalCase)
      {domain}        — stem with category suffix stripped and lowercased
                        e.g. HomeScreen → "home", LoginForm → "login", DashboardTable → "dashboard"
      {route}         — same as {domain}; use this for Expo Router file names where the
                        filename must be lowercase without the "Screen"/"View" suffix
    """
    categories = rules.get("categories", {})
    template = categories.get(category, {}).get("outputPath", "components/ui/{ComponentName}.tsx")
    path = template.replace("{ComponentName}", stem)
    if "{domain}" in path or "{route}" in path:
        # Strip the category suffix from stem to get a clean slug
        # e.g. HomeScreen → "home", LoginForm → "login", DashboardTable → "dashboard"
        slug = _derive_domain(stem) if category in ("screen", "widget", "feature") else stem.lower()
        path = path.replace("{domain}", slug).replace("{route}", slug)
    return path


def _customize_reference_files(output_map: dict, project_name: str, description: str = "") -> None:
    """Substitute __PROJECT_*__ placeholders in reference boilerplate files."""
    title = project_name.replace("-", " ").title()
    placeholder_map = {
        "__PROJECT_NAME__": project_name,
        "__PROJECT_TITLE__": title,
        "__PROJECT_DESCRIPTION__": description or f"{title} — generated from Figma Make by Nexus MCP",
        "@project-name/": f"@{project_name}/",
        "__YEAR__": str(datetime.datetime.now().year),
    }
    for path in list(output_map.keys()):
        content = output_map[path]
        for placeholder, value in placeholder_map.items():
            if placeholder in content:
                content = content.replace(placeholder, value)
        output_map[path] = content


def _load_agent_rules(golden_path: str) -> str:
    """Load the golden path agent markdown and return its content, or empty string.

    Checks two locations in order:
    1. tools/agents/ — packaged with the distribution (works after uvx install)
    2. .claude/agents/ — fallback for local dev (symlinks point back to tools/agents/)
    """
    candidates = [
        pathlib.Path(__file__).parent.parent / "agents" / f"{golden_path}.md",
        NEXUS_ROOT / ".claude" / "agents" / f"{golden_path}.md",
    ]
    for agent_file in candidates:
        try:
            return agent_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
    logger.warning(f"Agent file not found for golden path: {golden_path}")
    return ""


def _write_queue(
    cache_dir: pathlib.Path,
    llm_files: list[dict],
    golden_path: str,
    user_prompt: str,
    source_type: str = "figma",
) -> tuple[pathlib.Path, list[str]]:
    """
    Write one small markdown file per LLM file into 05_queue/.

    Each queue file is fully self-contained: it embeds the golden path agent
    rules inline so the agent needs no external file access to transform code.
    The agent reads them one at a time, transforms each component, updates
    04_file_tree.json, then deletes the queue file.
    Returns (queue_dir, sorted list of queue file names).

    source_type controls the queue file framing:
      "figma"  — "convert this Figma Make source" (default)
      "prompt" — "create this component from scratch based on the design spec"
    """
    queue_dir = cache_dir / "05_queue"
    # Wipe any stale queue from a previous run
    if queue_dir.exists():
        for old in queue_dir.iterdir():
            old.unlink()
    else:
        queue_dir.mkdir(parents=True)

    # Embed agent rules once — shared across all queue files for this run
    agent_rules = _load_agent_rules(golden_path)
    agent_rules_section = (
        f"\n\n---\n\n## Golden Path Rules ({golden_path})\n\n{agent_rules}"
        if agent_rules
        else ""
    )

    user_prompt_section = (
        f"\n\n## Additional Instructions\n\n{user_prompt}" if user_prompt.strip() else ""
    )

    # Build the project component list once — embedded in every queue file so the
    # agent knows exactly which paths are actual project components vs reference stubs,
    # even when earlier queue files have already been deleted.
    project_component_paths = [f["path"] for f in llm_files]
    project_components_line = (
        "**Project components:** "
        + ", ".join(f"`{p}`" for p in project_component_paths)
    ) if project_component_paths else ""

    queue_files: list[str] = []
    for idx, f in enumerate(llm_files, start=1):
        filename = f"{idx:03d}_{pathlib.Path(f['path']).stem}.md"

        if source_type == "prompt":
            task_verb = "Design"
            instructions = (
                f"1. Create this component **from scratch** based on the design specification below.\n"
                f"   - There is no Figma source — the spec is your only design input.\n"
                f"   - Invent appropriate visual design (colours, spacing, typography) that fits\n"
                f"     the project description and is consistent across all components.\n"
                f"   - Follow the **Golden Path Rules** section at the bottom of this file.\n"
            )
            source_heading = "### Design specification"
            source_fence = "```markdown"
        elif source_type == "codebase":
            task_verb = "Migrate"
            instructions = (
                f"1. Migrate the existing component below to enterprise-grade {golden_path} code.\n"
                f"   - Preserve the component's **UI, logic, and functionality** exactly.\n"
                f"   - Rewrite only what violates golden path conventions: TypeScript strictness,\n"
                f"     import paths, export style, `\"use client\"` placement, accessibility, naming.\n"
                f"   - Follow the **Golden Path Rules** section at the bottom of this file.\n"
            )
            source_heading = "### Existing source"
            source_fence = "```tsx"
        else:
            task_verb = "Transform"
            instructions = (
                f"1. Convert the Figma Make source below into enterprise-grade {golden_path} code.\n"
                f"   - Preserve the **exact same UI**: layout, content, styles, animations, design tokens.\n"
                f"   - Upgrade only the code quality: TypeScript types, proper imports, accessibility, file conventions.\n"
                f"   - Follow the **Golden Path Rules** section at the bottom of this file.\n"
            )
            source_heading = "### Figma Make source"
            source_fence = "```tsx"

        content = f"""\
## {task_verb} task {idx}/{len(llm_files)}: `{f['path']}`

**Golden path:** {golden_path}
**Source type:** {source_type}
**Category:** {f['category']}
**Output path:** `{f['path']}`
**File tree:** `{cache_dir}/04_file_tree.json`
**This queue file:** `{queue_dir}/{filename}`
{project_components_line}
{user_prompt_section}

### Instructions

{instructions}
   **SSR Safety:** Any access to `localStorage`, `sessionStorage`, `window`, or `document`
   outside of `useEffect` MUST be guarded:
   ```tsx
   // ✅ SSR-safe
   useState(() => typeof window !== "undefined" ? localStorage.getItem(key) : null)
   // or move to useEffect
   useEffect(() => {{ const val = localStorage.getItem(key); }}, [])
   ```
   Unguarded access will crash with `localStorage is not defined` during server rendering.

2. Update `{cache_dir}/04_file_tree.json`:
   - Read the JSON, find the entry whose `path` equals `{f['path']}`, replace its `content`.
   - If no entry exists yet, append `{{"path": "{f['path']}", "content": "<your output>"}}`.
   - Write the file back.
3. Delete this queue file (`{queue_dir}/{filename}`) once the update is confirmed written.
4. List the remaining files in `{queue_dir}/` and process the next one.
   Repeat until the queue directory is empty.

---

{source_heading}

{source_fence}
{f['figma_source']}
```
{agent_rules_section}
"""
        (queue_dir / filename).write_text(content, encoding="utf-8")
        queue_files.append(filename)
        logger.info(f"Queue file written: {filename} ({len(f['figma_source'])} chars)")

    return queue_dir, queue_files


def register_remap_tool(mcp: FastMCP) -> None:

    @mcp.tool()
    async def remap_to_golden_path(
        manifest_json: str,
        user_prompt: str = "",
    ) -> str:
        """
        Seed reference boilerplate, classify Figma files, and write the transformation queue.

        Takes the manifest from ingest_figma_zip, seeds the golden path reference
        boilerplate, auto-passes shadcn/ui primitives through, and writes one small
        queue file per component that needs LLM transformation into 05_queue/.

        The LLM agent reads queue files one at a time from the filesystem, transforms
        each component, updates 04_file_tree.json, deletes the queue file, and repeats
        until the queue directory is empty. This approach scales to any project size.

        Args:
            manifest_json: JSON string returned by ingest_figma_zip.
            user_prompt: Optional extra instructions for the LLM agent
                         (e.g. "add dark mode", "use Inter font").

        Returns:
            Slim summary with _nexus_cache pointer and agent instructions.
        """
        logger.info(
            "remap_to_golden_path called"
            + (f" - user_prompt: '{user_prompt[:80]}'" if user_prompt else "")
        )

        try:
            manifest = _load_input(manifest_json, "01_manifest.json")
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid manifest JSON: {str(e)}"})
        except Exception as e:
            return json.dumps({"error": f"Failed to load manifest: {str(e)}"})

        if "error" in manifest:
            return json.dumps({"error": f"Manifest contains error: {manifest['error']}"})

        golden_path = manifest.get("golden_path", "nextjs-fullstack")
        project_name = manifest.get("project_name", "my-app")
        source_type = manifest.get("source_type", "figma")

        # ── Load golden path manifest and classification rules ────────────────
        gp_manifest, rules = _load_golden_path_meta(golden_path)
        globals_css_file = gp_manifest.get("tailwind", {}).get("cssFile", "app/globals.css")
        # src_dir is "" for nextjs-* paths and "src/" for t3-stack, vite-spa, etc.
        src_dir = gp_manifest.get("routing", {}).get("srcDir", "")

        # ── 1. Seed output map with reference boilerplate ─────────────────────
        output_map: dict[str, str] = {}
        reference_paths: list[str] = []
        for ref_file in _load_reference_files(golden_path):
            output_map[ref_file["path"]] = ref_file["content"]
            reference_paths.append(ref_file["path"])

        # ── 2. Customise reference boilerplate with project details ──────────
        if "package.json" in output_map:
            try:
                pkg = json.loads(output_map["package.json"])
                pkg["name"] = project_name
                output_map["package.json"] = json.dumps(pkg, indent=2)
            except Exception:
                pass
        _customize_reference_files(output_map, project_name, manifest.get("description", ""))

        # ── 3. Classify Figma files ───────────────────────────────────────────
        all_figma_files = manifest.get("components", []) + manifest.get("pages", [])
        style_files = manifest.get("styles", [])

        llm_files: list[dict] = []
        passthrough_count = 0
        passthrough_paths: list[str] = []  # shadcn/ui files that were auto-cleaned (no LLM needed)
        detected_packages: dict[str, str] = {}  # package → version, read from Figma source

        # Pre-count pages so we can promote a sole page to root (app/page.tsx).
        # This ensures single-page apps always land at / regardless of their name
        # (e.g. "TodoPage" → app/page.tsx, not app/todo/page.tsx).
        page_stems = [
            comp["stem"] for comp in all_figma_files
            if _classify(comp["stem"], rules, golden_path) in ("page", "root_page")
        ]
        sole_page_stem = page_stems[0] if len(page_stems) == 1 else None

        for comp in all_figma_files:
            stem = comp["stem"]
            raw_content = comp.get("content", "")

            # Skip infra-content filter for non-Figma manifests:
            # - "prompt": content is a design spec, not source code with imports
            # - "codebase": existing components legitimately import Prisma/tRPC/etc.
            if source_type == "figma" and _is_infra_content(raw_content):
                logger.info(f"Discarding infra file by content: {stem}")
                continue

            category = _classify(stem, rules, golden_path)

            if category == "discard":
                logger.info(f"Discarding framework artifact: {stem}")
                continue

            if category == "root_page":
                routing_strategy = gp_manifest.get("routing", {}).get("strategy", "app-router")
                if routing_strategy == "app-router":
                    dest = f"{src_dir}app/page.tsx"
                else:
                    # Non-Next.js (e.g. vite-spa / react-router): use the page outputPath
                    # template with ComponentName=HomePage so it lands in the right place
                    # (e.g. src/routes/pages/HomePage.tsx for vite-spa).
                    page_tmpl = rules.get("categories", {}).get("page", {}).get(
                        "outputPath", f"{src_dir}app/page.tsx"
                    )
                    dest = page_tmpl.replace("{ComponentName}", "HomePage").replace("{route}", "").replace("{domain}", "")
                    dest = dest.replace("//", "/").rstrip("/")
            elif category == "section":
                section_template = rules.get("categories", {}).get("section", {}).get(
                    "outputPath", f"{src_dir}components/sections/{{ComponentName}}.tsx"
                )
                dest = section_template.replace("{ComponentName}", stem)
            elif category == "page":
                routing_strategy = gp_manifest.get("routing", {}).get("strategy", "app-router")
                if routing_strategy == "app-router":
                    # Single-page app: promote the only page to root regardless of its name
                    if sole_page_stem and stem == sole_page_stem:
                        dest = f"{src_dir}app/page.tsx"
                    else:
                        domain = _derive_domain(stem)
                        route = ROUTE_MAP.get(stem.lower()) or ROUTE_MAP.get(domain) or f"/{domain}"
                        dest = f"{src_dir}app/page.tsx" if route == "/" else f"{src_dir}app{route}/page.tsx"
                else:
                    # Non-app-router (e.g. react-router-v7): use the manifest outputPath template
                    dest = _resolve_output_path(stem, category, rules)
            else:
                dest = _resolve_output_path(stem, category, rules)

            # Shadcn/ui primitives: auto-passthrough — Figma ingestion only.
            # Skip for prompt/codebase: spec strings and real code need LLM migration.
            if source_type == "figma" and _is_shadcn_primitive(raw_content):
                # Extract versions from raw Figma source BEFORE cleaning strips them
                detected_packages.update(_extract_versioned_packages(raw_content))
                cleaned = _passthrough_shadcn(raw_content)
                # shadcn components ALWAYS land in {src_dir}components/ui/ (lowercase)
                # regardless of how _classify() categorized them — they are primitives,
                # not design sections, even if Figma put them in src/components/ui/.
                dest = f"{src_dir}components/ui/{stem.lower()}.tsx"
                output_map[dest] = cleaned
                passthrough_paths.append(dest)
                passthrough_count += 1
                logger.info(f"PASSTHROUGH (shadcn): {stem} -> {dest}")
                continue

            # components/ui/ enforces lowercase filenames (shadcn convention)
            if "/components/ui/" in dest or dest.startswith("components/ui/"):
                dir_part, file_part = dest.rsplit("/", 1)
                dest = f"{dir_part}/{file_part.lower()}"

            # All other files: queue for LLM transformation
            output_map[dest] = raw_content  # placeholder; agent will overwrite
            llm_files.append({
                "path": dest,
                "figma_source": raw_content,
                "category": category,
            })
            logger.info(f"{category.upper()}: {stem} -> {dest}")

        # ── Deduplicate llm_files by output path — last writer wins ──────────
        seen_paths: dict[str, dict] = {}
        for f in llm_files:
            seen_paths[f["path"]] = f
        llm_files = list(seen_paths.values())

        # ── 4. Add globals.css to queue (LLM extracts Figma design tokens) ───
        if style_files:
            figma_styles_content = "\n\n".join(
                f"/* --- {f.get('filename', 'style')} --- */\n{f.get('content', '')}"
                for f in style_files
            )
            llm_files.append({
                "path": globals_css_file,
                "figma_source": figma_styles_content,
                "category": "styles",
            })

        # ── 5. Move assets ────────────────────────────────────────────────────
        for asset in manifest.get("assets", []):
            from pathlib import PurePosixPath
            asset_name = PurePosixPath(asset["filename"]).name
            output_map[f"public/{asset_name}"] = BINARY_PLACEHOLDER

        # ── Inject packages discovered in passthrough files ───────────────────
        _inject_detected_packages(output_map, detected_packages)

        # ── Pre-flight: warn about requiredFiles missing from the seeded tree ─
        required_files: list[str] = gp_manifest.get("requiredFiles", [])
        missing_required = [r for r in required_files if r not in output_map]
        if missing_required:
            logger.warning(
                f"Pre-flight: {len(missing_required)} requiredFile(s) not seeded by reference/ "
                f"and not in Figma source — will fail validation unless the LLM agent creates them: "
                + ", ".join(missing_required)
            )

        # ── Serialize file tree (with placeholders for LLM files) ────────────
        output_files = [{"path": p, "content": c} for p, c in output_map.items()]
        result = {
            "project_name": project_name,
            "golden_path": golden_path,
            "total_files": len(output_files),
            "passthrough_paths": passthrough_paths,
            "reference_paths": reference_paths,
            "files": output_files,
        }

        cache_dir = pathlib.Path(f"/tmp/nexus-{project_name}")
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "04_file_tree.json").write_text(json.dumps(result), encoding="utf-8")

        # ── 6. Write one queue file per LLM file ─────────────────────────────
        queue_dir, queue_files = _write_queue(cache_dir, llm_files, golden_path, user_prompt, source_type)

        logger.info(
            f"remap_to_golden_path complete — {len(output_files)} total files, "
            f"{passthrough_count} shadcn passthrough, {len(llm_files)} queued for LLM"
        )

        # Queue items: metadata only — agents read content from disk via path.
        # Omitting inline content keeps the response small (queue files can be
        # large markdown blobs; 20 files × 8 KB = ~160 KB of unnecessary payload).
        # n8n / API-only clients should use the update_file_in_tree tool and
        # read queue files via the server filesystem or a dedicated read tool.
        queue_items = []
        for filename in queue_files:
            queue_items.append({
                "filename": filename,
                "path": str(queue_dir / filename),
            })

        return json.dumps({
            "project_name": project_name,
            "golden_path": golden_path,
            "total_files": len(output_files),
            "passthrough_count": passthrough_count,
            "queue_count": len(llm_files),
            "missing_required_preflight": missing_required,
            "queue_dir": str(queue_dir),
            "queue_files": queue_files,
            "queue_items": queue_items,
            "_nexus_cache": str(cache_dir),
            "_instructions": (
                f"Spawn the '{golden_path}' agent. "
                f"It reads queue files from {queue_dir}/ one at a time (they are self-contained). "
                f"For each: transform the component, update {cache_dir}/04_file_tree.json, "
                f"delete the queue file, then process the next. "
                f"Repeat until {queue_dir}/ is empty, then call package_output."
            ),
        })
