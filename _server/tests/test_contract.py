import pytest

from app.contract import Access, ContractError, parse_contract

SAMPLE = """---
bootstrap: true
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 01_intended-use.md
    relative_to: run
---
# 01_intended-use

Some prose.
"""


def test_parses_bootstrap_flag_and_inputs():
    contract = parse_contract(SAMPLE)
    assert contract.bootstrap is True
    assert len(contract.inputs) == 3
    run_md = contract.inputs[0]
    assert run_md.path == "RUN.md"
    assert run_md.relative_to == "run"
    assert run_md.access == Access.READ_WRITE
    assert run_md.optional is False
    house = contract.inputs[2]
    assert house.optional is True


def test_parses_outputs_and_prose():
    contract = parse_contract(SAMPLE)
    assert contract.outputs[0].path == "01_intended-use.md"
    assert "# 01_intended-use" in contract.prose
    assert "---" not in contract.prose.split("\n")[0]


def test_directory_paths_are_detected():
    contract = parse_contract(SAMPLE.replace(
        "  - path: 01_intended-use.md\n    relative_to: run",
        "  - path: build/items/\n    relative_to: run",
    ))
    assert contract.outputs[0].is_directory is True


def test_missing_frontmatter_raises():
    with pytest.raises(ContractError):
        parse_contract("# no frontmatter here\n")


def test_unterminated_frontmatter_raises():
    with pytest.raises(ContractError):
        parse_contract("---\nbootstrap: true\n# never closed\n")
