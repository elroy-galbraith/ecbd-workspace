from pathlib import Path

import pytest

from app.approval import ApprovalError, approve_stage, reject_stage
from app.scope import load_stage_scope


def _prepare_stage_01_run(tmp_repo: Path) -> Path:
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text(
        "| File | Stage | Questions | Done |\n"
        "|---|---|---|---|\n"
        "| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |\n"
        "\n## Loop-backs\n\n"
        "| Date | From stage | Back to stage | What forced it | What changed |\n"
        "|---|---|---|---|---|\n",
        encoding="utf-8"
    )
    return run_root


def test_approve_fails_when_output_missing(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )
    with pytest.raises(ApprovalError):
        approve_stage(scope, "01")


def test_approve_ticks_run_md_when_output_exists(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    (run_root / "01_intended-use.md").write_text("the intended use, in full")
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )

    result = approve_stage(scope, "01")

    assert result.approved_stage == "01"
    assert "[x]" in (run_root / "RUN.md").read_text()


def test_approve_fails_on_empty_output(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    (run_root / "01_intended-use.md").write_text("")
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )
    with pytest.raises(ApprovalError):
        approve_stage(scope, "01")


def test_reject_unticks_and_adds_loop_back_row(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    (run_root / "01_intended-use.md").write_text("the intended use")
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )
    approve_stage(scope, "01")

    reject_stage(scope, from_stage="01", target_stage="01", reason="vague decision")

    text = (run_root / "RUN.md").read_text()
    assert "[ ]" in text
    assert "vague decision" in text
