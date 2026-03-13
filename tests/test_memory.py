"""Unit tests for tools/devsecops/memory.py"""

import pathlib
import re

import pytest

from tools.devsecops.memory import (
    _first_meaningful_line,
    _key80,
    _parse_frontmatter,
    _scan_triggers,
    build_memory_context_block,
    read_memory,
    update_memory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter_val(text: str, key: str) -> str:
    fm, _ = _parse_frontmatter(text)
    return fm.get(key, "")


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


def test_parse_frontmatter_basic():
    raw = "---\nname: test\nrun_count: 3\n---\n\nbody here\n"
    fm, body = _parse_frontmatter(raw)
    assert fm["name"] == "test"
    assert fm["run_count"] == "3"
    assert "body here" in body


def test_parse_frontmatter_no_frontmatter():
    raw = "just body text"
    fm, body = _parse_frontmatter(raw)
    assert fm == {}
    assert body == raw


# ---------------------------------------------------------------------------
# _scan_triggers
# ---------------------------------------------------------------------------


def test_scan_triggers_detects_keyword():
    text = "We should migrate the auth module to OAuth2."
    hits = _scan_triggers(text)
    assert len(hits) == 1
    assert "migrate" in hits[0].lower()


def test_scan_triggers_deduplicates():
    text = "We should migrate auth.\nWe should migrate auth."
    hits = _scan_triggers(text)
    assert len(hits) == 1


def test_scan_triggers_no_hits():
    hits = _scan_triggers("This is a simple change with no major keywords.")
    assert hits == []


# ---------------------------------------------------------------------------
# _key80
# ---------------------------------------------------------------------------


def test_key80_normalises_whitespace():
    assert _key80("  hello   world  ") == "hello world"


def test_key80_truncates_to_80():
    long = "x" * 200
    assert len(_key80(long)) == 80


# ---------------------------------------------------------------------------
# _first_meaningful_line
# ---------------------------------------------------------------------------


def test_first_meaningful_line_skips_headers():
    text = "# Header\n\nThis is the real content line."
    assert _first_meaningful_line(text) == "This is the real content line."


def test_first_meaningful_line_empty():
    assert _first_meaningful_line("") == ""


# ---------------------------------------------------------------------------
# update_memory + read_memory — solo layout
# ---------------------------------------------------------------------------


def test_update_creates_personal_file(tmp_path):
    memory_dir = str(tmp_path / "agents")
    ok, pending = update_memory(memory_dir, "code-reviewer", "Found no issues.")
    assert ok
    # Default write target is personal/ (team-ready from day one)
    personal = tmp_path / "agents" / "personal" / "code-reviewer.md"
    assert personal.exists()


def test_update_increments_run_count(tmp_path):
    memory_dir = str(tmp_path / "agents")
    update_memory(memory_dir, "security", "Issue A.")
    update_memory(memory_dir, "security", "Issue B.")
    personal = tmp_path / "agents" / "personal" / "security.md"
    assert personal.exists()
    text = _read_file(personal)
    assert _frontmatter_val(text, "run_count") == "2"


def test_update_recent_findings_rolling_window(tmp_path):
    memory_dir = str(tmp_path / "agents")
    for i in range(5):
        update_memory(memory_dir, "qa-tester", f"Finding number {i}: something important here.")
    personal = tmp_path / "agents" / "personal" / "qa-tester.md"
    text = _read_file(personal)
    # Only 3 recent findings kept
    recent_count = text.count("- [")
    # recent findings plus any pending items
    fm, body = _parse_frontmatter(text)
    recent_section = re.search(
        r"## Recent Findings\n(.*?)(?=^## |\Z)", body, re.DOTALL | re.MULTILINE
    )
    if recent_section:
        lines = [l for l in recent_section.group(1).splitlines() if l.strip().startswith("- [")]
        assert len(lines) <= 3


def test_update_trigger_adds_pending_item(tmp_path):
    memory_dir = str(tmp_path / "agents")
    update_memory(memory_dir, "code-reviewer", "We should migrate the DB layer to Drizzle ORM.")
    personal = tmp_path / "agents" / "personal" / "code-reviewer.md"
    text = _read_file(personal)
    assert "⚠️ Pending Human Review" in text
    assert "- [ ]" in text


def test_update_pending_item_not_duplicated(tmp_path):
    memory_dir = str(tmp_path / "agents")
    msg = "We should migrate the DB layer to Drizzle ORM."
    update_memory(memory_dir, "code-reviewer", msg)
    update_memory(memory_dir, "code-reviewer", msg)
    personal = tmp_path / "agents" / "personal" / "code-reviewer.md"
    text = _read_file(personal)
    assert text.count("- [ ]") == 1


def test_update_mode_reset(tmp_path):
    memory_dir = str(tmp_path / "agents")
    update_memory(memory_dir, "security", "Some findings here to keep track of.")
    update_memory(memory_dir, "security", "", mode="reset")
    personal = tmp_path / "agents" / "personal" / "security.md"
    text = _read_file(personal)
    assert _frontmatter_val(text, "run_count") == "0"
    fm, body = _parse_frontmatter(text)
    assert "Recent Findings" in body
    # Body should be blank (no actual content lines)
    for section_body in re.findall(r"## \S.*?\n(.*?)(?=^## |\Z)", body, re.DOTALL | re.MULTILINE):
        assert section_body.strip() == ""


def test_update_mode_replace(tmp_path):
    memory_dir = str(tmp_path / "agents")
    update_memory(memory_dir, "monitoring", "Original findings.", mode="replace")
    update_memory(memory_dir, "monitoring", "Replaced content.", mode="replace")
    personal = tmp_path / "agents" / "personal" / "monitoring.md"
    text = _read_file(personal)
    assert "Replaced content." in text
    assert "Original findings." not in text


# ---------------------------------------------------------------------------
# read_memory
# ---------------------------------------------------------------------------


def test_read_memory_returns_none_when_no_files(tmp_path):
    result = read_memory(str(tmp_path / "agents"), "nonexistent")
    assert result is None


def test_read_memory_returns_content_after_write(tmp_path):
    memory_dir = str(tmp_path / "agents")
    update_memory(memory_dir, "database", "Schema looks fine.")
    result = read_memory(memory_dir, "database")
    assert result is not None
    assert "database" in result.lower() or "Schema" in result


# ---------------------------------------------------------------------------
# build_memory_context_block
# ---------------------------------------------------------------------------


def test_build_context_block_empty_when_no_memory(tmp_path):
    block = build_memory_context_block(str(tmp_path / "agents"), "code-reviewer")
    assert block == ""


def test_build_context_block_contains_agent_header(tmp_path):
    memory_dir = str(tmp_path / "agents")
    update_memory(memory_dir, "code-reviewer", "Found a potential SQL injection risk in routes.")
    block = build_memory_context_block(memory_dir, "code-reviewer")
    assert "Past Memory (code-reviewer)" in block
    assert "End of past memory" in block


def test_build_context_block_merges_shared_and_personal(tmp_path):
    memory_dir = str(tmp_path / "agents")
    shared_dir = tmp_path / "agents" / "shared"
    shared_dir.mkdir(parents=True)
    (shared_dir / "security.md").write_text(
        "---\nname: security memory\ntype: agent-memory\nagent: security\n"
        "project: test\ncreated: 2026-01-01\nlast_updated: 2026-01-01\nrun_count: 1\n---\n\n"
        "## Recent Findings\n\n- [2026-01-01] Team shared finding.\n",
        encoding="utf-8",
    )
    update_memory(memory_dir, "security", "Personal finding about auth token expiry.")
    block = build_memory_context_block(memory_dir, "security")
    assert "Shared team memory" in block
    assert "Personal memory" in block
    assert "Team shared finding" in block
    assert "Personal finding" in block


# ---------------------------------------------------------------------------
# Auto-gitignore
# ---------------------------------------------------------------------------


def test_auto_gitignore_added_on_first_personal_write(tmp_path):
    # Simulate a git repo
    (tmp_path / ".git").mkdir()
    memory_dir = str(tmp_path / ".claude" / "memory" / "agents")
    update_memory(memory_dir, "code-reviewer", "Found issue.")
    gitignore = tmp_path / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text()
    assert "personal" in content


def test_auto_gitignore_not_duplicated(tmp_path):
    (tmp_path / ".git").mkdir()
    memory_dir = str(tmp_path / ".claude" / "memory" / "agents")
    update_memory(memory_dir, "code-reviewer", "First run.")
    update_memory(memory_dir, "code-reviewer", "Second run.")
    gitignore = tmp_path / ".gitignore"
    content = gitignore.read_text()
    # personal/ entry should appear exactly once
    assert content.count("personal/") == 1
