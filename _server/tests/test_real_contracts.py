from pathlib import Path

import pytest

from app.contract import parse_contract
from app.scope import load_stage_scope

REPO_ROOT = Path(__file__).resolve().parents[2]

STAGES = [
    "01_intended-use", "02_capability", "03_content", "04_adaptation",
    "05_assembly", "06_evidence", "07_validity-review", "08_build",
]


@pytest.mark.parametrize("stage", STAGES)
def test_every_design_stage_contract_has_valid_frontmatter(stage: str):
    contract_path = REPO_ROOT / "01-design" / stage / "CONTEXT.md"
    text = contract_path.read_text(encoding="utf-8")
    contract = parse_contract(text)  # raises ContractError if malformed
    assert contract.outputs, f"{stage} declares no outputs"


def test_stage_01_is_the_only_bootstrap_stage():
    for stage in STAGES:
        contract_path = REPO_ROOT / "01-design" / stage / "CONTEXT.md"
        contract = parse_contract(contract_path.read_text(encoding="utf-8"))
        assert contract.bootstrap == (stage == "01_intended-use"), stage


def test_stage_02_scope_resolves_against_a_fabricated_run(tmp_path: Path):
    run_root = tmp_path / "worksheets" / "design-fixture"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("state")
    (run_root / "01_intended-use.md").write_text("intended use")
    scope = load_stage_scope(
        REPO_ROOT / "01-design" / "02_capability" / "CONTEXT.md",
        repo_root=REPO_ROOT,
        run_root=run_root,
    )
    assert scope.resolve_readable("_shared/capability-conventions.md").exists()
    assert scope.resolve_writable("02_capability.md") == (run_root / "02_capability.md").resolve()


def test_stage_03_has_a_stage_relative_reference_and_a_directory_output(tmp_path: Path):
    run_root = tmp_path / "worksheets" / "design-fixture"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("state")
    (run_root / "02_capability.md").write_text("capabilities")
    scope = load_stage_scope(
        REPO_ROOT / "01-design" / "03_content" / "CONTEXT.md",
        repo_root=REPO_ROOT,
        run_root=run_root,
    )
    assert scope.resolve_readable("references/item-design.md").exists()
    assert scope.resolve_writable("build/items/example.json") == (
        run_root / "build" / "items" / "example.json"
    ).resolve()
