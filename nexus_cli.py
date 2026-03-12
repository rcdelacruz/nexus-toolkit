"""
nexus — CLI for the Nexus Design-to-Code pipeline.

Usage:
  nexus ingest zip <zip_path> --golden-path <gp> [--project-name <name>]
  nexus ingest prompt "<description>" --golden-path <gp> [--project-name <name>]
  nexus ingest codebase <dir> --golden-path <gp> [--project-name <name>]
  nexus remap <project_name> [--prompt "<text>"]
  nexus transform <project_name> [--model <model>]
  nexus validate <project_name>
  nexus package <project_name>
  nexus run zip <zip_path> --golden-path <gp> [--project-name <name>] [--prompt "<text>"]
  nexus run prompt "<description>" --golden-path <gp> [--project-name <name>] [--prompt "<text>"]
  nexus run codebase <dir> --golden-path <gp> [--project-name <name>] [--prompt "<text>"]

All commands read from / write to /tmp/nexus-<project_name>/ automatically.
"""

import asyncio
import base64
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Annotated, Optional

import typer
from rich import box
from rich.console import Console
from rich.live import Live
from rich.padding import Padding
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# ── Bootstrap: capture MCP tools without starting the server ─────────────────


class _MockMCP:
    """Minimal stand-in for FastMCP that captures @mcp.tool() decorated functions."""

    def __init__(self) -> None:
        self._tools: dict = {}

    def tool(self):
        def decorator(fn):
            self._tools[fn.__name__] = fn
            return fn

        return decorator


def _load_tools() -> dict:
    """Import all tool modules and collect their async functions."""
    from tools.figma.codebase_ingest import register_codebase_ingest_tool
    from tools.figma.ingest import register_ingest_tool
    from tools.figma.package import register_package_tool
    from tools.figma.prompt_ingest import register_prompt_ingest_tool
    from tools.figma.remap import register_remap_tool
    from tools.figma.validate import register_validate_tool

    mock = _MockMCP()
    register_ingest_tool(mock)
    register_prompt_ingest_tool(mock)
    register_codebase_ingest_tool(mock)
    register_remap_tool(mock)
    register_validate_tool(mock)
    register_package_tool(mock)
    return mock._tools


_tools: dict = {}


def _get_tools() -> dict:
    global _tools
    if not _tools:
        _tools = _load_tools()
    return _tools


# ── Theme & console ───────────────────────────────────────────────────────────

_THEME = Theme({
    "success": "bold green",
    "error": "bold red",
    "warn": "bold yellow",
    "muted": "dim white",
    "step": "bold cyan",
    "brand": "bold white",
    "path": "cyan underline",
})

console = Console(theme=_THEME)


_VERSION = "2.2.0"

_LOGO = """\
[cyan]███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗[/cyan]
[cyan]████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝[/cyan]
[cyan]██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗[/cyan]
[cyan]██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║[/cyan]
[cyan]██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║[/cyan]
[cyan]╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/cyan]
[dim white]enterprise dev toolkit[/dim white]  [dim cyan]v{version}[/dim cyan]"""


def _print_header(project: str, golden_path: str, source: str) -> None:
    """Print the pipeline run header banner."""
    console.print()
    console.print(Padding(_LOGO.format(version=_VERSION), (0, 2)))
    console.print()
    console.print(Rule(style="bright_black"))
    console.print()

    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="dim white", min_width=12)
    meta.add_column(style="white")
    meta.add_row("project", f"[bold]{project}[/bold]")
    meta.add_row("golden path", f"[cyan]{golden_path}[/cyan]")
    meta.add_row("source", source)
    console.print(Padding(meta, (0, 2)))
    console.print()


def _step_done(n: int, total: int, label: str, detail: str = "") -> None:
    detail_str = f"  [dim]{detail}[/dim]" if detail else ""
    console.print(f"  [green]●[/green]  [bold]{label}[/bold]{detail_str}")


def _step_skip(label: str, detail: str = "") -> None:
    detail_str = f"  [dim]{detail}[/dim]" if detail else ""
    console.print(f"  [bright_black]○[/bright_black]  [dim]{label}[/dim]{detail_str}")


def _step_run(label: str) -> str:
    """Return a running-step line prefix (caller prints after done)."""
    return f"  [cyan]◆[/cyan]  [bold]{label}[/bold]"


def _step_error(label: str, detail: str = "") -> None:
    detail_str = f"  [dim]{detail}[/dim]" if detail else ""
    console.print(f"  [red]✗[/red]  [bold red]{label}[/bold red]{detail_str}")


def _print_success(zip_path: pathlib.Path, total_files: int, size_kb: int) -> None:
    console.print()
    console.print(Rule(style="bright_black"))
    console.print()
    result = Table.grid(padding=(0, 2))
    result.add_column(style="dim white", min_width=10)
    result.add_column(style="white")
    result.add_row("output", f"[cyan underline]{zip_path}[/cyan underline]")
    result.add_row("files", str(total_files))
    result.add_row("size", f"{size_kb} KB")
    console.print(Panel(
        result,
        title="[bold green] pipeline complete [/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(0, 1),
    ))
    console.print()


def _print_errors(errors: list, warnings: list, project_name: str) -> None:
    console.print()
    console.print(Rule(style="bright_black"))
    lines = []
    for e in errors[:15]:
        lines.append(Text.assemble(("  ✗ ", "bold red"), (e, "white")))
    for w in warnings[:5]:
        lines.append(Text.assemble(("  ⚠ ", "bold yellow"), (w, "dim white")))
    content = "\n".join(str(l) for l in lines)
    console.print(Panel(
        "\n".join(f"  [red]✗[/red] {e}" for e in errors[:15]) +
        ("" if not warnings else "\n" + "\n".join(f"  [yellow]⚠[/yellow] {w}" for w in warnings[:5])),
        title="[bold red] validation failed [/bold red]",
        border_style="red",
        box=box.ROUNDED,
        padding=(0, 1),
    ))
    console.print(f"\n  Fix errors then run: [bold]nexus validate {project_name}[/bold]\n")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _cache_json(project_name: str) -> str:
    """Return the minimal JSON needed to point validate/package at the cache."""
    return json.dumps({"_nexus_cache": f"/tmp/nexus-{project_name}"})


def _parse_result(raw: str, step: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        _step_error(step, "returned non-JSON output")
        raise typer.Exit(1)
    if "error" in data:
        _step_error(step, data["error"])
        raise typer.Exit(1)
    return data


def _summary_table(data: dict) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim white", min_width=14)
    table.add_column(style="white")
    for k, v in data.items():
        if k.startswith("_") or isinstance(v, (list, dict)):
            continue
        table.add_row(k, str(v))
    console.print(Padding(table, (0, 4)))


_NEXUS_ROOT = pathlib.Path(__file__).parent
_AGENTS_DIR = _NEXUS_ROOT / "tools" / "agents"


def _find_claude(claude_path: Optional[str] = None) -> str:
    """Return path to the claude CLI, or raise if not found.

    Resolution order:
    1. --claude-path flag / explicit argument
    2. CLAUDE_PATH environment variable
    3. PATH (shutil.which)
    4. ~/.local/bin/claude (standard Claude Code install on macOS/Linux)
    """
    import os

    candidate = claude_path or os.environ.get("CLAUDE_PATH")
    if candidate:
        p = pathlib.Path(candidate).expanduser()
        if p.exists():
            return str(p)
        console.print(f"[red]✗ claude CLI not found at:[/red] {p}")
        raise typer.Exit(1)

    via_which = shutil.which("claude")
    if via_which:
        return via_which

    fallback = pathlib.Path.home() / ".local" / "bin" / "claude"
    if fallback.exists():
        return str(fallback)

    console.print(
        "[red]✗ claude CLI not found.[/red]\n"
        "  Install Claude Code or set [bold]CLAUDE_PATH[/bold] / use [bold]--claude-path[/bold]."
    )
    raise typer.Exit(1)


_DECOMPOSE_SYSTEM = """\
You are a UI decomposition assistant. Given a natural-language description of an app or page,
return a JSON object with two keys:
  - "pages": list of PascalCase page component names (e.g. ["ProfilePage"])
  - "components": list of PascalCase section/UI component names (e.g. ["ProfileCard", "SkillsSection"])

Rules:
- pages are top-level route components (Page suffix)
- components are reusable sections or UI pieces rendered inside pages
- Return ONLY valid JSON, no markdown, no explanation
- If the description is a scaffold request with no specific UI, return {"pages": [], "components": []}
"""


def _decompose_description(description: str, claude_bin: str, model: str) -> tuple[list[str], list[str]]:
    """Call claude CLI to decompose a description into pages and components."""
    import subprocess
    result = subprocess.run(
        [claude_bin, "--print", "--model", model, "--system-prompt", _DECOMPOSE_SYSTEM, description],
        capture_output=True, text=True,
    )
    output = result.stdout.strip()
    # Strip markdown code fences if present
    if output.startswith("```"):
        output = "\n".join(output.split("\n")[1:])
        output = output.rsplit("```", 1)[0].strip()
    try:
        data = json.loads(output)
        return data.get("pages", []), data.get("components", [])
    except (json.JSONDecodeError, AttributeError):
        console.print(f"[yellow]⚠ Could not parse decomposition, using description as-is[/yellow]")
        return [], []


def _find_agent(golden_path: str) -> pathlib.Path:
    """Return path to the golden-path agent markdown file."""
    agent = _AGENTS_DIR / f"{golden_path}.md"
    if agent.exists():
        return agent
    # When installed via uvx, search relative to this file's installed location
    for candidate in pathlib.Path(__file__).parent.rglob(f"agents/{golden_path}.md"):
        return candidate
    console.print(f"[red]✗ Agent file not found for golden path:[/red] {golden_path}")
    raise typer.Exit(1)


def _get_golden_path_from_cache(project_name: str) -> str:
    """Read golden_path from the cached 01_manifest.json."""
    manifest = pathlib.Path(f"/tmp/nexus-{project_name}/01_manifest.json")
    if not manifest.exists():
        console.print(f"[red]✗ No cache found for project:[/red] {project_name}  (run ingest first)")
        raise typer.Exit(1)
    return json.loads(manifest.read_text())["golden_path"]


# ── Typer apps ────────────────────────────────────────────────────────────────

app = typer.Typer(
    name="nexus",
    no_args_is_help=False,
    pretty_exceptions_enable=False,
    invoke_without_command=True,
    add_help_option=False,
    rich_markup_mode="rich",
)
ingest_app = typer.Typer(help="Ingest source files into the Nexus pipeline.", no_args_is_help=True)
run_app = typer.Typer(help="Run the full pipeline end-to-end.", no_args_is_help=True)
agent_app = typer.Typer(help="Run dev-workflow agents (code review, security, QA, etc.).", no_args_is_help=True)
workflow_app = typer.Typer(help="Run slash-command workflows (review, deploy, docs, etc.).", no_args_is_help=True)
app.add_typer(ingest_app, name="ingest")
app.add_typer(run_app, name="run")
app.add_typer(agent_app, name="agent")
app.add_typer(workflow_app, name="workflow")


def _print_help() -> None:
    """Fully Rich-rendered help + examples (bypasses Click's word-wrap)."""
    # Commands table
    cmds = Table(box=box.ROUNDED, border_style="bright_black", padding=(0, 1), show_header=False, expand=False)
    cmds.add_column(style="cyan", no_wrap=True)
    cmds.add_column(style="dim white")
    cmds.add_row("ingest zip",    "Ingest a Figma ZIP export")
    cmds.add_row("ingest prompt", "Ingest from a text description")
    cmds.add_row("ingest codebase", "Ingest an existing project for migration")
    cmds.add_row("remap",         "Seed boilerplate + write transformation queue")
    cmds.add_row("transform",     "Process queue files with Claude (LLM step)")
    cmds.add_row("validate",      "Validate output for production readiness")
    cmds.add_row("package",       "Package output into a ZIP")
    cmds.add_row("run zip",       "Full pipeline from a Figma ZIP")
    cmds.add_row("run prompt",    "Full pipeline from a text description")
    cmds.add_row("run codebase",  "Full pipeline from an existing codebase")
    cmds.add_row("agent list",    "List available dev-workflow agents")
    cmds.add_row("agent run",     "Run an agent against a file or diff")
    cmds.add_row("workflow run",  "Run a slash-command workflow")
    console.print(Padding("[bold]Commands[/bold]", (0, 2)))
    console.print(Padding(cmds, (0, 2)))
    console.print()

    # Examples
    examples = [
        ("[dim]# one-liner — full pipeline[/dim]", ""),
        ("[cyan]nexus run prompt[/cyan]", '[white]"A SaaS dashboard"[/white] [dim]-g nextjs-fullstack -p my-app[/dim]'),
        ("[cyan]nexus run zip[/cyan]",    "[white]~/Downloads/export.zip[/white] [dim]-g nextjs-static -p landing[/dim]"),
        ("[cyan]nexus run codebase[/cyan]", "[white]~/projects/old-app[/white] [dim]-g nextjs-fullstack[/dim]"),
        ("", ""),
        ("[dim]# step-by-step[/dim]", ""),
        ("[cyan]nexus ingest prompt[/cyan]", '[white]"A todo app"[/white] [dim]-g vite-spa -p todos[/dim]'),
        ("[cyan]nexus remap[/cyan]",       "[white]todos[/white]"),
        ("[cyan]nexus transform[/cyan]",   "[white]todos[/white]"),
        ("[cyan]nexus validate[/cyan]",    "[white]todos[/white]"),
        ("[cyan]nexus package[/cyan]",     "[white]todos[/white] [dim]-o ~/Desktop/[/dim]"),
    ]
    console.print(Padding("[bold]Examples[/bold]", (0, 2)))
    for cmd, args in examples:
        line = f"    {cmd} {args}" if args else f"    {cmd}"
        console.print(line, highlight=False, no_wrap=True)
    console.print()

    # Common flags
    flags = Table(box=box.SIMPLE, padding=(0, 1), show_header=False, expand=False)
    flags.add_column(style="cyan", no_wrap=True)
    flags.add_column(style="dim white", no_wrap=True)
    flags.add_column(style="white")
    flags.add_row("-g, --golden-path",  "TEXT",  "Target stack (nextjs-fullstack, nextjs-static, t3-stack, vite-spa, monorepo, full-stack-rn, full-stack-flutter)")
    flags.add_row("-p, --project-name", "TEXT",  "Project slug — used for cache dir and output ZIP name")
    flags.add_row("-m, --model",        "TEXT",  "Claude model for transform step  [default: claude-sonnet-4-6]")
    flags.add_row("    --prompt",       "TEXT",  "Extra instructions passed to the LLM agent")
    flags.add_row("    --claude-path",  "PATH",  "Path to claude CLI  (or set CLAUDE_PATH env var)")
    flags.add_row("-o, --output-dir",   "PATH",  "Copy final ZIP to this directory")
    flags.add_row("-h, --help",         "",      "Show this message and exit")
    console.print(Padding("[bold]Common flags[/bold]", (0, 2)))
    console.print(Padding(flags, (0, 2)))
    console.print(Padding("[dim]Run [bold]nexus COMMAND --help[/bold] for per-command options.[/dim]", (0, 2)))
    console.print()


def _check_update() -> None:
    """Check PyPI for a newer version and print a warning if one exists. Silent on failure."""
    try:
        import urllib.request
        with urllib.request.urlopen("https://pypi.org/pypi/nexus-toolkit/json", timeout=2) as resp:
            data = json.loads(resp.read())
        latest = data["info"]["version"]
        if latest != _VERSION:
            console.print(
                f"  [yellow]⚠ Update available:[/yellow] [dim]{_VERSION}[/dim] → [bold cyan]{latest}[/bold cyan]"
                "  run [bold]nexus update[/bold] to upgrade"
            )
            console.print()
    except Exception:
        pass


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    help: bool = typer.Option(False, "--help", "-h", is_eager=True, expose_value=True, is_flag=True, help="Show this message and exit."),
    version: bool = typer.Option(False, "--version", "-v", is_eager=True, expose_value=True, is_flag=True, help="Print version and exit."),
) -> None:
    """"""
    console.print()
    console.print(Padding(_LOGO.format(version=_VERSION), (0, 2)))
    console.print()
    if version:
        raise typer.Exit()
    _check_update()
    if help or ctx.invoked_subcommand is None:
        _print_help()
        raise typer.Exit()

# ── nexus update ─────────────────────────────────────────────────────────────


@app.command("update")
def update() -> None:
    """Upgrade nexus-toolkit to the latest version from PyPI."""
    import subprocess
    installer = shutil.which("uv")
    if installer:
        cmd = ["uv", "tool", "install", "--reinstall", "--force", "nexus-toolkit"]
    else:
        cmd = ["pip3", "install", "--upgrade", "nexus-toolkit"]

    console.print(f"  [cyan]▶[/cyan]  Upgrading nexus-toolkit…")
    result = subprocess.run(cmd)
    if result.returncode == 0:
        console.print("  [green]✓[/green]  Updated successfully — restart your shell to use the new version.")
    else:
        console.print("  [red]✗[/red]  Update failed.")
        raise typer.Exit(1)


# ── nexus version ────────────────────────────────────────────────────────────


@app.command("version")
def version_cmd() -> None:
    """Print the current version."""
    console.print(f"  nexus-toolkit [bold cyan]{_VERSION}[/bold cyan]")


# ── nexus ingest zip ──────────────────────────────────────────────────────────


@ingest_app.command("zip")
def ingest_zip(
    zip_path: Annotated[pathlib.Path, typer.Argument(help="Path to the Figma-export ZIP file.")],
    golden_path: Annotated[str, typer.Option("--golden-path", "-g", help="Target golden path.")],
    project_name: Annotated[
        Optional[str], typer.Option("--project-name", "-p", help="Project slug (default: zip stem).")
    ] = None,
):
    """Ingest a Figma ZIP export."""
    if not zip_path.exists():
        console.print(f"[red]✗ File not found:[/red] {zip_path}")
        raise typer.Exit(1)

    resolved_name = project_name or zip_path.stem
    zip_b64 = base64.b64encode(zip_path.read_bytes()).decode()

    tools = _get_tools()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task(f"  reading {zip_path.name}…")
        raw = asyncio.run(tools["ingest_figma_zip"](zip_b64, "", golden_path, resolved_name))

    data = _parse_result(raw, "ingest zip")
    summary = data.get("summary", {})
    _step_done(1, 1, "ingest", f"{summary.get('components', 0)} components · {summary.get('pages', 0)} pages")
    console.print()
    _summary_table(summary)


# ── nexus ingest prompt ───────────────────────────────────────────────────────


@ingest_app.command("prompt")
def ingest_prompt(
    description: Annotated[str, typer.Argument(help="Natural-language description of the app.")],
    golden_path: Annotated[str, typer.Option("--golden-path", "-g", help="Target golden path.")],
    project_name: Annotated[
        Optional[str], typer.Option("--project-name", "-p", help="Project slug.")
    ] = None,
):
    """Ingest from a text description (no design files needed)."""
    resolved_name = project_name or "my-app"

    tools = _get_tools()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  inferring components from description…")
        raw = asyncio.run(tools["ingest_from_prompt"](description, golden_path, resolved_name))

    data = _parse_result(raw, "ingest prompt")
    summary = data.get("summary", {})
    _step_done(1, 1, "ingest", f"{summary.get('components', 0)} components · {summary.get('pages', 0)} pages")
    console.print()
    _summary_table(summary)


# ── nexus ingest codebase ─────────────────────────────────────────────────────


@ingest_app.command("codebase")
def ingest_codebase(
    project_dir: Annotated[pathlib.Path, typer.Argument(help="Path to the existing project root.")],
    golden_path: Annotated[str, typer.Option("--golden-path", "-g", help="Target golden path.")],
    project_name: Annotated[
        Optional[str], typer.Option("--project-name", "-p", help="Project slug (default: dir name).")
    ] = None,
):
    """Ingest an existing codebase for migration to a golden path."""
    if not project_dir.exists():
        console.print(f"[red]✗ Directory not found:[/red] {project_dir}")
        raise typer.Exit(1)

    resolved_name = project_name or project_dir.name

    tools = _get_tools()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task(f"  scanning {project_dir.name}/…")
        raw = asyncio.run(tools["ingest_from_codebase"](str(project_dir), golden_path, resolved_name))

    data = _parse_result(raw, "ingest codebase")
    summary = data.get("summary", {})
    _step_done(1, 1, "ingest", f"{summary.get('components', 0)} components · {summary.get('pages', 0)} pages · {summary.get('skipped_config', 0)} config skipped")
    console.print()
    _summary_table(summary)


# ── nexus remap ───────────────────────────────────────────────────────────────


@app.command()
def remap(
    project_name: Annotated[str, typer.Argument(help="Project slug (matches /tmp/nexus-<name>).")],
    prompt: Annotated[
        Optional[str], typer.Option("--prompt", "-m", help="Extra instructions for the LLM agent.")
    ] = None,
):
    """Seed reference boilerplate and write the transformation queue."""
    manifest_json = _cache_json(project_name)

    tools = _get_tools()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  seeding boilerplate + building queue…")
        raw = asyncio.run(tools["remap_to_golden_path"](manifest_json, prompt or ""))

    data = _parse_result(raw, "remap")
    cache = data.get("_nexus_cache", f"/tmp/nexus-{project_name}")
    queue_dir = pathlib.Path(cache) / "05_queue"
    queue_count = len(list(queue_dir.glob("*.md"))) if queue_dir.exists() else 0

    _step_done(1, 1, "remap", f"{queue_count} queue file(s) → {cache}/05_queue/")
    if queue_count > 0:
        console.print()
        console.print(f"  [dim]next:[/dim] [bold]nexus transform {project_name}[/bold]")


# ── nexus transform ───────────────────────────────────────────────────────────


@app.command()
def transform(
    project_name: Annotated[str, typer.Argument(help="Project slug (matches /tmp/nexus-<name>).")],
    model: Annotated[
        str, typer.Option("--model", "-m", help="Claude model to use.")
    ] = "claude-sonnet-4-6",
    claude_path: Annotated[
        Optional[str], typer.Option("--claude-path", help="Path to claude CLI. Overrides CLAUDE_PATH env var.")
    ] = None,
):
    """
    Run the LLM transformation step: process all queue files with Claude.

    Requires the `claude` CLI (Claude Code) to be installed.
    Processes every file in 05_queue/ using the golden-path agent as system prompt,
    updates 04_file_tree.json, and deletes each queue file when done.
    """
    cache = pathlib.Path(f"/tmp/nexus-{project_name}")
    queue_dir = cache / "05_queue"

    if not cache.exists():
        console.print(f"[red]✗ No cache found:[/red] {cache}  (run ingest + remap first)")
        raise typer.Exit(1)

    queue_files = sorted(queue_dir.glob("*.md")) if queue_dir.exists() else []
    if not queue_files:
        console.print(f"[yellow]⚠  No queue files in {queue_dir} — nothing to transform.[/yellow]")
        return

    golden_path = _get_golden_path_from_cache(project_name)
    agent_file = _find_agent(golden_path)
    claude_bin = _find_claude(claude_path)

    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="dim white", min_width=10)
    meta.add_column(style="white")
    meta.add_row("project", f"[bold]{project_name}[/bold]")
    meta.add_row("golden path", f"[cyan]{golden_path}[/cyan]")
    meta.add_row("model", model)
    meta.add_row("queue", f"{len(queue_files)} file(s)")
    console.print()
    console.print(Panel(meta, title="[bold] nexus transform [/bold]", box=box.ROUNDED, border_style="bright_black", padding=(0, 1)))
    console.print()

    prompt = (
        f"Process all queue files in {queue_dir}/ following the instructions embedded in each file.\n"
        f"Start with the first file in alphabetical order and continue until the queue is empty.\n"
        f"The full file tree is at {cache}/04_file_tree.json."
    )

    cmd = [
        claude_bin,
        "--print",
        "--dangerously-skip-permissions",
        "--model", model,
        "--system-prompt", agent_file.read_text(encoding="utf-8"),
        prompt,
        "--add-dir", str(cache),
    ]

    console.print(Rule("claude", style="bright_black"))
    console.print()
    try:
        result = subprocess.run(cmd, text=True, capture_output=False)
    except KeyboardInterrupt:
        console.print()
        console.print(Rule(style="bright_black"))
        console.print(f"\n  [yellow]⚠[/yellow]  interrupted\n")
        raise typer.Exit(1)

    console.print()
    console.print(Rule(style="bright_black"))

    if result.returncode != 0:
        _step_error("transform", f"claude exited with code {result.returncode}")
        raise typer.Exit(result.returncode)

    remaining = list(queue_dir.glob("*.md")) if queue_dir.exists() else []
    if remaining:
        console.print(f"\n  [yellow]⚠[/yellow]  {len(remaining)} queue file(s) remain — run transform again\n")
    else:
        _step_done(1, 1, "transform", "queue empty")
        console.print(f"\n  [dim]next:[/dim] [bold]nexus validate {project_name}[/bold]\n")


# ── nexus validate ────────────────────────────────────────────────────────────


@app.command()
def validate(
    project_name: Annotated[str, typer.Argument(help="Project slug (matches /tmp/nexus-<name>).")],
):
    """Validate the generated file tree for production readiness."""
    file_tree_json = _cache_json(project_name)

    tools = _get_tools()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  checking imports, required files, code quality…")
        raw = asyncio.run(tools["validate_output"](file_tree_json))

    data = _parse_result(raw, "validate")
    passed = data.get("passed", False)
    errors = data.get("errors", [])
    warnings = data.get("warnings", [])

    if passed:
        _step_done(1, 1, "validate", f"passed · {data.get('warning_count', 0)} warning(s)")
        if warnings:
            console.print()
            for w in warnings:
                console.print(f"    [yellow]⚠[/yellow]  [dim]{w}[/dim]")
    else:
        _print_errors(errors, warnings, project_name)
        raise typer.Exit(1)


# ── nexus package ─────────────────────────────────────────────────────────────


@app.command()
def package(
    project_name: Annotated[str, typer.Argument(help="Project slug (matches /tmp/nexus-<name>).")],
    output_dir: Annotated[
        Optional[pathlib.Path],
        typer.Option("--output-dir", "-o", help="Where to copy the ZIP (default: current dir)."),
    ] = None,
):
    """Package the file tree into a downloadable ZIP."""
    file_tree_json = _cache_json(project_name)

    tools = _get_tools()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  writing ZIP…")
        raw = asyncio.run(tools["package_output"](file_tree_json))

    data = _parse_result(raw, "package")
    zip_path = pathlib.Path(data.get("zip_path", ""))

    dest = zip_path
    if output_dir:
        dest = pathlib.Path(output_dir) / zip_path.name
        shutil.copy2(zip_path, dest)

    size_kb = data.get("size_bytes", 0) // 1024
    _step_done(1, 1, "package", f"{data.get('total_files', '?')} files · {size_kb} KB")
    _print_success(dest, data.get("total_files", 0), size_kb)


# ── nexus run zip ─────────────────────────────────────────────────────────────


@run_app.command("zip")
def run_zip(
    zip_path: Annotated[pathlib.Path, typer.Argument(help="Path to the Figma-export ZIP file.")],
    golden_path: Annotated[str, typer.Option("--golden-path", "-g", help="Target golden path.")],
    project_name: Annotated[
        Optional[str], typer.Option("--project-name", "-p", help="Project slug.")
    ] = None,
    prompt: Annotated[
        Optional[str], typer.Option("--prompt", help="Extra instructions for the LLM agent.")
    ] = None,
    model: Annotated[
        str, typer.Option("--model", "-m", help="Claude model to use for transformation.")
    ] = "claude-sonnet-4-6",
    claude_path: Annotated[
        Optional[str], typer.Option("--claude-path", help="Path to claude CLI. Overrides CLAUDE_PATH env var.")
    ] = None,
    output_dir: Annotated[
        Optional[pathlib.Path],
        typer.Option("--output-dir", "-o", help="Where to copy the final ZIP."),
    ] = None,
):
    """Run the full pipeline from a Figma ZIP (ingest → remap → [LLM] → validate → package)."""
    if not zip_path.exists():
        console.print(f"[red]✗ File not found:[/red] {zip_path}")
        raise typer.Exit(1)

    resolved_name = project_name or zip_path.stem
    zip_b64 = base64.b64encode(zip_path.read_bytes()).decode()

    tools = _get_tools()
    _run_pipeline(tools, resolved_name, golden_path, prompt, output_dir, model, claude_path,
                  ingest_coro=tools["ingest_figma_zip"](zip_b64, "", golden_path, resolved_name))


# ── nexus run prompt ──────────────────────────────────────────────────────────


@run_app.command("prompt")
def run_prompt(
    description: Annotated[str, typer.Argument(help="Natural-language description of the app.")],
    golden_path: Annotated[str, typer.Option("--golden-path", "-g", help="Target golden path.")],
    project_name: Annotated[
        Optional[str], typer.Option("--project-name", "-p", help="Project slug.")
    ] = None,
    prompt: Annotated[
        Optional[str], typer.Option("--prompt", help="Extra LLM instructions.")
    ] = None,
    model: Annotated[
        str, typer.Option("--model", "-m", help="Claude model to use for transformation.")
    ] = "claude-sonnet-4-6",
    claude_path: Annotated[
        Optional[str], typer.Option("--claude-path", help="Path to claude CLI. Overrides CLAUDE_PATH env var.")
    ] = None,
    output_dir: Annotated[
        Optional[pathlib.Path],
        typer.Option("--output-dir", "-o", help="Where to copy the final ZIP."),
    ] = None,
):
    """Run the full pipeline from a text description."""
    resolved_name = project_name or "my-app"
    claude_bin = _find_claude(claude_path)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  decomposing description…")
        pages, components = _decompose_description(description, claude_bin, model)

    console.print(f"  [dim]pages:[/dim] {pages or '—'}  [dim]components:[/dim] {components or '—'}")

    tools = _get_tools()
    _run_pipeline(tools, resolved_name, golden_path, prompt, output_dir, model, claude_path,
                  ingest_coro=tools["ingest_from_prompt"](description, golden_path, resolved_name, pages, components))


# ── nexus run codebase ────────────────────────────────────────────────────────


@run_app.command("codebase")
def run_codebase(
    project_dir: Annotated[pathlib.Path, typer.Argument(help="Path to the existing project root.")],
    golden_path: Annotated[str, typer.Option("--golden-path", "-g", help="Target golden path.")],
    project_name: Annotated[
        Optional[str], typer.Option("--project-name", "-p", help="Project slug.")
    ] = None,
    prompt: Annotated[
        Optional[str], typer.Option("--prompt", help="Extra LLM instructions.")
    ] = None,
    model: Annotated[
        str, typer.Option("--model", "-m", help="Claude model to use for transformation.")
    ] = "claude-sonnet-4-6",
    claude_path: Annotated[
        Optional[str], typer.Option("--claude-path", help="Path to claude CLI. Overrides CLAUDE_PATH env var.")
    ] = None,
    output_dir: Annotated[
        Optional[pathlib.Path],
        typer.Option("--output-dir", "-o", help="Where to copy the final ZIP."),
    ] = None,
):
    """Run the full pipeline from an existing codebase."""
    if not project_dir.exists():
        console.print(f"[red]✗ Directory not found:[/red] {project_dir}")
        raise typer.Exit(1)

    resolved_name = project_name or project_dir.name
    tools = _get_tools()
    _run_pipeline(tools, resolved_name, golden_path, prompt, output_dir, model, claude_path,
                  ingest_coro=tools["ingest_from_codebase"](str(project_dir), golden_path, resolved_name))


# ── Shared pipeline runner ────────────────────────────────────────────────────


def _run_pipeline(tools, project_name, golden_path, user_prompt, output_dir, model, claude_path, ingest_coro):
    """Execute ingest → remap → transform → validate → package."""
    _print_header(project_name, golden_path, "pipeline")

    # Step 1: ingest
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  1/4  ingesting…")
        raw = asyncio.run(ingest_coro)
    data = _parse_result(raw, "ingest")
    summary = data.get("summary", {})
    _step_done(1, 4, "ingest", f"{summary.get('components', 0)} components · {summary.get('pages', 0)} pages")

    # Step 2: remap
    manifest_json = _cache_json(project_name)
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  2/4  remapping to golden path…")
        raw = asyncio.run(tools["remap_to_golden_path"](manifest_json, user_prompt or ""))
    remap_data = _parse_result(raw, "remap")
    cache = remap_data.get("_nexus_cache", f"/tmp/nexus-{project_name}")
    queue_dir = pathlib.Path(cache) / "05_queue"
    queue_count = len(list(queue_dir.glob("*.md"))) if queue_dir.exists() else 0
    _step_done(2, 4, "remap", f"{queue_count} queue file(s)")

    if queue_count > 0:
        # Step 3: transform
        gp = remap_data.get("golden_path", _get_golden_path_from_cache(project_name))
        agent_file = _find_agent(gp)
        claude_bin = _find_claude(claude_path)

        prompt = (
            f"Process all queue files in {cache}/05_queue/ following the instructions embedded in each file.\n"
            f"Start with the first file in alphabetical order and continue until the queue is empty.\n"
            f"The full file tree is at {cache}/04_file_tree.json."
        )
        cmd = [
            claude_bin,
            "--print",
            "--dangerously-skip-permissions",
            "--model", model,
            "--system-prompt", agent_file.read_text(encoding="utf-8"),
            prompt,
            "--add-dir", str(cache),
        ]
        console.print(f"  [cyan]◆[/cyan]  [bold]transform[/bold]  [dim]running claude ({model})…[/dim]")
        console.print()
        console.print(Rule("claude", style="bright_black"))
        console.print()
        try:
            result = subprocess.run(cmd, text=True, capture_output=False)
        except KeyboardInterrupt:
            console.print()
            console.print(Rule(style="bright_black"))
            console.print(f"\n  [yellow]⚠[/yellow]  interrupted\n")
            raise typer.Exit(1)
        console.print()
        console.print(Rule(style="bright_black"))
        console.print()
        if result.returncode != 0:
            _step_error("transform", f"claude exited with code {result.returncode}")
            raise typer.Exit(result.returncode)
        _step_done(3, 4, "transform", "queue empty")
    else:
        _step_skip("transform", "no queue files")

    _validate_and_package(tools, project_name, output_dir, cache)


def _validate_and_package(tools, project_name, output_dir, cache):
    file_tree_json = _cache_json(project_name)

    # Validate
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  4/4  validating…")
        raw = asyncio.run(tools["validate_output"](file_tree_json))
    val_data = _parse_result(raw, "validate")
    passed = val_data.get("passed", False)
    errors = val_data.get("errors", [])
    warnings = val_data.get("warnings", [])
    if not passed:
        _step_error("validate", f"{val_data.get('error_count', 0)} error(s)")
        _print_errors(errors, warnings, project_name)
        raise typer.Exit(1)
    _step_done(4, 4, "validate", f"passed · {val_data.get('warning_count', 0)} warning(s)")

    # Package
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task("  5/5  packaging…")
        raw = asyncio.run(tools["package_output"](file_tree_json))
    pkg_data = _parse_result(raw, "package")
    zip_path = pathlib.Path(pkg_data.get("zip_path", ""))

    dest = zip_path
    if output_dir:
        dest = pathlib.Path(output_dir) / zip_path.name
        shutil.copy2(zip_path, dest)

    size_kb = pkg_data.get("size_bytes", 0) // 1024
    _step_done(5, 5, "package", f"{pkg_data.get('total_files', '?')} files · {size_kb} KB")
    _print_success(dest, pkg_data.get("total_files", 0), size_kb)


# ── Dev-agent helpers ─────────────────────────────────────────────────────────

_DEV_AGENTS_DIR = _NEXUS_ROOT / "tools" / "dev-agents"

_DEV_AGENT_REGISTRY: dict[str, str] = {
    "code-reviewer": "cross-cutting",
    "database": "cross-cutting",
    "deployment": "cross-cutting",
    "monitoring": "cross-cutting",
    "performance": "cross-cutting",
    "product-manager": "cross-cutting",
    "qa-tester": "cross-cutting",
    "security": "cross-cutting",
    "task-planner": "cross-cutting",
    "tech-writer": "cross-cutting",
    "test-planner": "cross-cutting",
    "software-architect": "architecture",
    "solution-architect": "architecture",
    "solution-designer": "architecture",
    "backend-api": "javascript",
    "frontend-ui": "javascript",
    "fullstack-nextjs": "javascript",
    "react-native": "javascript",
    "savant-fullstack-js": "savants",
    "savant-flutter": "savants",
    "savant-java-spring": "savants",
    "savant-react-native": "savants",
}


def _find_dev_agent(agent_name: str) -> pathlib.Path:
    """Return path to the dev-workflow agent markdown file."""
    subdir = _DEV_AGENT_REGISTRY.get(agent_name)
    if subdir:
        candidate = _DEV_AGENTS_DIR / subdir / f"{agent_name}.md"
        if candidate.exists():
            return candidate
    for p in _DEV_AGENTS_DIR.rglob(f"{agent_name}.md"):
        return p
    # uvx-installed fallback
    for p in pathlib.Path(__file__).parent.rglob(f"dev-agents/**/{agent_name}.md"):
        return p
    available = ", ".join(sorted(_DEV_AGENT_REGISTRY.keys()))
    console.print(f"[red]✗ Agent not found:[/red] {agent_name}")
    console.print(f"  Available: [dim]{available}[/dim]")
    raise typer.Exit(1)


def _find_workflow(workflow_name: str) -> pathlib.Path:
    """Return path to a workflow markdown file."""
    candidates = [
        _NEXUS_ROOT / ".claude" / "commands" / f"{workflow_name}.md",
        _NEXUS_ROOT / "docs" / "sample-claude-agents" / "commands" / f"{workflow_name}.md",
    ]
    for p in candidates:
        if p.exists():
            return p
    workflows = sorted(p.stem for p in (_NEXUS_ROOT / ".claude" / "commands").glob("*.md"))
    console.print(f"[red]✗ Workflow not found:[/red] {workflow_name}")
    console.print(f"  Available: [dim]{', '.join(workflows)}[/dim]")
    raise typer.Exit(1)


# ── nexus agent list ──────────────────────────────────────────────────────────


@agent_app.command("list")
def agent_list() -> None:
    """List all available dev-workflow agents."""
    by_category: dict[str, list[str]] = {}
    for name, cat in sorted(_DEV_AGENT_REGISTRY.items()):
        by_category.setdefault(cat, []).append(name)

    console.print()
    for cat in sorted(by_category.keys()):
        table = Table(box=box.SIMPLE, padding=(0, 1), show_header=False, expand=False)
        table.add_column(style="cyan", no_wrap=True)
        for name in sorted(by_category[cat]):
            table.add_row(name)
        console.print(Padding(f"[bold]{cat}[/bold]", (0, 2)))
        console.print(Padding(table, (0, 4)))
    console.print()


# ── nexus agent run ───────────────────────────────────────────────────────────


@agent_app.command("run")
def agent_run(
    agent_name: Annotated[str, typer.Argument(help="Agent name (e.g. code-reviewer, security).")],
    file_path: Annotated[
        Optional[pathlib.Path],
        typer.Argument(help="File to analyze (reads content as context). Use '-' to read from stdin."),
    ] = None,
    context: Annotated[
        Optional[str], typer.Option("--context", "-c", help="Inline context string instead of a file.")
    ] = None,
    model: Annotated[
        str, typer.Option("--model", "-m", help="Claude model to use.")
    ] = "claude-sonnet-4-6",
    claude_path: Annotated[
        Optional[str], typer.Option("--claude-path", help="Path to claude CLI.")
    ] = None,
) -> None:
    """Run a dev-workflow agent (e.g. code-reviewer, security) against a file or inline context."""
    import sys as _sys

    agent_file = _find_dev_agent(agent_name)

    if context:
        input_text = context
        source_label = "inline context"
    elif file_path and str(file_path) == "-":
        input_text = _sys.stdin.read()
        source_label = "stdin"
    elif file_path:
        if not file_path.exists():
            console.print(f"[red]✗ File not found:[/red] {file_path}")
            raise typer.Exit(1)
        input_text = file_path.read_text(encoding="utf-8", errors="replace")
        source_label = str(file_path)
    else:
        console.print("[red]✗ Provide a file path or --context string.[/red]")
        raise typer.Exit(1)

    claude_bin = _find_claude(claude_path)

    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="dim white", min_width=10)
    meta.add_column(style="white")
    meta.add_row("agent", f"[cyan]{agent_name}[/cyan]")
    meta.add_row("source", source_label)
    meta.add_row("model", model)
    console.print()
    console.print(Panel(meta, title="[bold] nexus agent run [/bold]", box=box.ROUNDED, border_style="bright_black", padding=(0, 1)))
    console.print()

    cmd = [
        claude_bin,
        "--print",
        "--dangerously-skip-permissions",
        "--model", model,
        "--system-prompt", agent_file.read_text(encoding="utf-8"),
        input_text,
    ]

    console.print(Rule(agent_name, style="bright_black"))
    console.print()
    try:
        result = subprocess.run(cmd, text=True, capture_output=False)
    except KeyboardInterrupt:
        console.print()
        console.print(f"\n  [yellow]⚠[/yellow]  interrupted\n")
        raise typer.Exit(1)

    console.print()
    console.print(Rule(style="bright_black"))
    if result.returncode != 0:
        _step_error("agent run", f"claude exited with code {result.returncode}")
        raise typer.Exit(result.returncode)


# ── nexus workflow run ────────────────────────────────────────────────────────


@workflow_app.command("run")
def workflow_run(
    workflow_name: Annotated[str, typer.Argument(help="Workflow name (e.g. workflow-review-code, workflow-deploy).")],
    file_path: Annotated[
        Optional[pathlib.Path],
        typer.Argument(help="File to analyze as context. Use '-' to read from stdin."),
    ] = None,
    context: Annotated[
        Optional[str], typer.Option("--context", "-c", help="Inline context string.")
    ] = None,
    model: Annotated[
        str, typer.Option("--model", "-m", help="Claude model to use.")
    ] = "claude-sonnet-4-6",
    claude_path: Annotated[
        Optional[str], typer.Option("--claude-path", help="Path to claude CLI.")
    ] = None,
) -> None:
    """Run a slash-command workflow (e.g. workflow-review-code, workflow-deploy) against a file."""
    import sys as _sys

    workflow_file = _find_workflow(workflow_name)
    workflow_text = workflow_file.read_text(encoding="utf-8")

    if context:
        input_text = f"{workflow_text}\n\n---\n\n## Context:\n\n{context}"
        source_label = "inline context"
    elif file_path and str(file_path) == "-":
        file_content = _sys.stdin.read()
        input_text = f"{workflow_text}\n\n---\n\n## Context:\n\n{file_content}"
        source_label = "stdin"
    elif file_path:
        if not file_path.exists():
            console.print(f"[red]✗ File not found:[/red] {file_path}")
            raise typer.Exit(1)
        file_content = file_path.read_text(encoding="utf-8", errors="replace")
        input_text = f"{workflow_text}\n\n---\n\n## Context:\n\n{file_content}"
        source_label = str(file_path)
    else:
        # No context provided — just run the workflow instructions
        input_text = workflow_text
        source_label = "workflow only"

    claude_bin = _find_claude(claude_path)

    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="dim white", min_width=10)
    meta.add_column(style="white")
    meta.add_row("workflow", f"[cyan]{workflow_name}[/cyan]")
    meta.add_row("source", source_label)
    meta.add_row("model", model)
    console.print()
    console.print(Panel(meta, title="[bold] nexus workflow run [/bold]", box=box.ROUNDED, border_style="bright_black", padding=(0, 1)))
    console.print()

    cmd = [
        claude_bin,
        "--print",
        "--dangerously-skip-permissions",
        "--model", model,
        input_text,
    ]

    console.print(Rule(workflow_name, style="bright_black"))
    console.print()
    try:
        result = subprocess.run(cmd, text=True, capture_output=False)
    except KeyboardInterrupt:
        console.print()
        console.print(f"\n  [yellow]⚠[/yellow]  interrupted\n")
        raise typer.Exit(1)

    console.print()
    console.print(Rule(style="bright_black"))
    if result.returncode != 0:
        _step_error("workflow run", f"claude exited with code {result.returncode}")
        raise typer.Exit(result.returncode)


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    app()


if __name__ == "__main__":
    main()
