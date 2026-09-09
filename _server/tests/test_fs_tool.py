from pathlib import Path

import pytest

from app.contract import parse_contract
from app.fs_tool import ScopedFilesystemTool, ScopeError
from app.scope import StageScope

CONTRACT = """---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 01_intended-use.md
    relative_to: run
    access: read
outputs:
  - path: 02_capability.md
    relative_to: run
  - path: build/items/
    relative_to: run
---
prose
"""


@pytest.fixture
def tool(tmp_path: Path) -> ScopedFilesystemTool:
    run_root = tmp_path / "worksheets" / "design-test"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("| 01 | [ ] |\n")
    (run_root / "01_intended-use.md").write_text("intended use")
    scope = StageScope(
        contract=parse_contract(CONTRACT),
        repo_root=tmp_path,
        stage_dir=tmp_path / "01-design" / "02_capability",
        run_root=run_root,
    )
    scope._rebuild()
    return ScopedFilesystemTool(scope)


def test_reads_a_declared_input(tool: ScopedFilesystemTool):
    assert tool.read_file("01_intended-use.md") == "intended use"


def test_reads_outside_scope_raises(tool: ScopedFilesystemTool):
    with pytest.raises(ScopeError):
        tool.read_file("../../secrets.md")


def test_writes_a_declared_output(tool: ScopedFilesystemTool, tmp_path: Path):
    tool.write_file("02_capability.md", "capability card")
    written = tmp_path / "worksheets" / "design-test" / "02_capability.md"
    assert written.read_text() == "capability card"


def test_writes_to_a_read_only_input_raises(tool: ScopedFilesystemTool):
    with pytest.raises(ScopeError):
        tool.write_file("01_intended-use.md", "overwritten")


def test_writes_into_a_declared_directory(tool: ScopedFilesystemTool, tmp_path: Path):
    tool.write_file("build/items/item-001.json", "{}")
    written = tmp_path / "worksheets" / "design-test" / "build" / "items" / "item-001.json"
    assert written.read_text() == "{}"


def test_edit_file_replaces_first_occurrence(tool: ScopedFilesystemTool, tmp_path: Path):
    tool.write_file("02_capability.md", "draft: todo\nmore text")
    tool.edit_file("02_capability.md", "draft: todo", "draft: done")
    written = tmp_path / "worksheets" / "design-test" / "02_capability.md"
    assert written.read_text() == "draft: done\nmore text"


def test_edit_file_missing_old_text_raises(tool: ScopedFilesystemTool):
    tool.write_file("02_capability.md", "hello")
    with pytest.raises(ScopeError):
        tool.edit_file("02_capability.md", "not present", "new")


# --- approved_stages guard -------------------------------------------------
#
# approved_stages: in RUN.md's frontmatter is meant to be a fact only
# approve_stage/reject_stage (human-invoked, via app/approval.py) can write
# -- never a model-exposed tool. These tests guard against a regression
# where write_file/edit_file could rewrite it directly.


@pytest.fixture
def tool_with_approval_marker(tmp_path: Path) -> ScopedFilesystemTool:
    run_root = tmp_path / "worksheets" / "design-test"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text(
        "---\napproved_stages: []\n---\n\n# Title\n\n| 01 | [ ] |\n"
    )
    (run_root / "01_intended-use.md").write_text("intended use")
    scope = StageScope(
        contract=parse_contract(CONTRACT),
        repo_root=tmp_path,
        stage_dir=tmp_path / "01-design" / "02_capability",
        run_root=run_root,
    )
    scope._rebuild()
    return ScopedFilesystemTool(scope)


def test_edit_file_cannot_change_approved_stages(tool_with_approval_marker: ScopedFilesystemTool, tmp_path: Path):
    run_md = tmp_path / "worksheets" / "design-test" / "RUN.md"
    with pytest.raises(ScopeError):
        tool_with_approval_marker.edit_file(
            "RUN.md", "approved_stages: []", 'approved_stages: ["01"]'
        )
    assert "approved_stages: []" in run_md.read_text()
    assert '"01"' not in run_md.read_text()


def test_write_file_cannot_change_approved_stages(tool_with_approval_marker: ScopedFilesystemTool, tmp_path: Path):
    run_md = tmp_path / "worksheets" / "design-test" / "RUN.md"
    original = run_md.read_text()
    with pytest.raises(ScopeError):
        tool_with_approval_marker.write_file(
            "RUN.md", "---\napproved_stages: [\"01\"]\n---\n\n# Title\n\n| 01 | [ ] |\n"
        )
    assert run_md.read_text() == original


def test_edit_file_can_still_change_other_run_md_content(tool_with_approval_marker: ScopedFilesystemTool, tmp_path: Path):
    run_md = tmp_path / "worksheets" / "design-test" / "RUN.md"
    tool_with_approval_marker.edit_file("RUN.md", "# Title", "# My Eval")
    assert "# My Eval" in run_md.read_text()
    assert "approved_stages: []" in run_md.read_text()


def test_edit_file_can_still_tick_stage_table_in_run_md(tool_with_approval_marker: ScopedFilesystemTool, tmp_path: Path):
    run_md = tmp_path / "worksheets" / "design-test" / "RUN.md"
    tool_with_approval_marker.edit_file("RUN.md", "| 01 | [ ] |", "| 01 | [x] |")
    assert "| 01 | [x] |" in run_md.read_text()
    assert "approved_stages: []" in run_md.read_text()


def test_write_file_can_still_change_other_run_md_content(tool_with_approval_marker: ScopedFilesystemTool, tmp_path: Path):
    run_md = tmp_path / "worksheets" / "design-test" / "RUN.md"
    tool_with_approval_marker.write_file(
        "RUN.md", "---\napproved_stages: []\n---\n\n# New Title\n\n| 01 | [ ] |\n"
    )
    assert "# New Title" in run_md.read_text()
    assert "approved_stages: []" in run_md.read_text()


def test_write_file_to_run_md_without_approval_marker_still_works(tool: ScopedFilesystemTool, tmp_path: Path):
    # The default `tool` fixture's RUN.md ("| 01 | [ ] |\n") has no
    # approved_stages: line at all -- the guard must not block ordinary
    # writes to a RUN.md that carries no approval marker to protect.
    tool.write_file("RUN.md", "| 01 | [x] |\n")
    written = tmp_path / "worksheets" / "design-test" / "RUN.md"
    assert written.read_text() == "| 01 | [x] |\n"


def test_edit_file_to_run_md_without_approval_marker_still_works(tool: ScopedFilesystemTool, tmp_path: Path):
    tool.edit_file("RUN.md", "[ ]", "[x]")
    written = tmp_path / "worksheets" / "design-test" / "RUN.md"
    assert written.read_text() == "| 01 | [x] |\n"
