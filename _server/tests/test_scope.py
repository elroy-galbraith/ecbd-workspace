from pathlib import Path

import pytest

from app.contract import ContractError
from app.scope import StageScope, load_stage_scope

CONTRACT = """---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 01_intended-use.md
    relative_to: run
    access: read
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
  - path: references/item-design.md
    relative_to: stage
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
def repo(tmp_path: Path) -> Path:
    (tmp_path / "_shared").mkdir()
    (tmp_path / "_shared" / "ecbd-framework.md").write_text("framework")
    stage_dir = tmp_path / "01-design" / "02_capability"
    stage_dir.mkdir(parents=True)
    (stage_dir / "CONTEXT.md").write_text(CONTRACT)
    (stage_dir / "references").mkdir()
    (stage_dir / "references" / "item-design.md").write_text("item design notes")
    run_root = tmp_path / "worksheets" / "design-test"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("run state")
    (run_root / "01_intended-use.md").write_text("intended use")
    return tmp_path


def test_resolves_all_three_bases(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)

    assert scope.resolve_readable("RUN.md") == (run_root / "RUN.md").resolve()
    assert scope.resolve_readable("_shared/ecbd-framework.md") == (repo / "_shared" / "ecbd-framework.md").resolve()
    assert scope.resolve_readable("references/item-design.md") == (
        repo / "01-design" / "02_capability" / "references" / "item-design.md"
    ).resolve()


def test_optional_missing_input_is_silently_dropped(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    with pytest.raises(ContractError):
        scope.resolve_readable("_shared/house-context.md")


def test_required_missing_input_raises(repo: Path):
    (repo / "worksheets" / "design-test" / "01_intended-use.md").unlink()
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    with pytest.raises(ContractError):
        load_stage_scope(contract_path, repo_root=repo, run_root=run_root)


def test_read_write_access_makes_a_path_writable(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    assert scope.resolve_writable("RUN.md") == (run_root / "RUN.md").resolve()
    with pytest.raises(ContractError):
        scope.resolve_writable("_shared/ecbd-framework.md")


def test_declared_output_is_writable_even_though_not_yet_created(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    assert scope.resolve_writable("02_capability.md") == (run_root / "02_capability.md").resolve()


def test_directory_output_accepts_any_file_beneath_it(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    assert scope.resolve_writable("build/items/item-001.json") == (
        run_root / "build" / "items" / "item-001.json"
    ).resolve()


def test_directory_traversal_out_of_a_declared_directory_is_rejected(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    with pytest.raises(ContractError):
        scope.resolve_writable("build/items/../../secrets.md")


def test_bootstrap_stage_defers_run_relative_paths_until_bound(tmp_path: Path):
    (tmp_path / "_shared").mkdir()
    (tmp_path / "_shared" / "ecbd-framework.md").write_text("framework")
    stage_dir = tmp_path / "01-design" / "01_intended-use"
    stage_dir.mkdir(parents=True)
    (stage_dir / "CONTEXT.md").write_text("""---
bootstrap: true
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
outputs:
  - path: 01_intended-use.md
    relative_to: run
---
prose
""")
    scope = load_stage_scope(stage_dir / "CONTEXT.md", repo_root=tmp_path, run_root=None)
    with pytest.raises(ContractError):
        scope.resolve_readable("RUN.md")

    run_root = tmp_path / "worksheets" / "design-test"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("run state")
    scope.bind_run_root(run_root)
    assert scope.resolve_readable("RUN.md") == (run_root / "RUN.md").resolve()
