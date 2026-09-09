from pathlib import Path

import pytest

from app.approval import ApprovalError, approve_stage, reject_stage
from app.scope import load_stage_scope


def _prepare_stage_01_run(tmp_repo: Path) -> Path:
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text(
        "---\n"
        "slug: design-my-eval\n"
        "approved_stages: []\n"
        "---\n"
        "| File | Stage | Questions | Done |\n"
        "|---|---|---|---|\n"
        "| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |\n"
        "| `02_capability.md` | 02 | Q3–Q5 | [ ] |\n"
        "| `03_content.md` | 03 | Q6–Q8 | [ ] |\n"
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
    text = (run_root / "RUN.md").read_text()
    assert "[x]" in text
    assert 'approved_stages: ["01"]' in text


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

    reject_stage(scope, stages_to_untick=["01"], target_stage="01", reason="vague decision")

    text = (run_root / "RUN.md").read_text(encoding="utf-8")
    assert "| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |" in text
    assert "vague decision" in text
    assert 'approved_stages: []' in text


def test_reject_from_stage_3_back_to_1_unticks_and_removes_all_three(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )
    text = (run_root / "RUN.md").read_text(encoding="utf-8")
    from app.run_md import add_approved_stage, tick_stage

    for stage in ("01", "02", "03"):
        text = tick_stage(text, stage)
        text = add_approved_stage(text, stage)
    (run_root / "RUN.md").write_text(text, encoding="utf-8")

    reject_stage(
        scope,
        stages_to_untick=["01", "02", "03"],
        target_stage="01",
        reason="capability drifted after content review",
    )

    result_text = (run_root / "RUN.md").read_text(encoding="utf-8")
    for stage_row, label in (
        ("| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |", "01"),
        ("| `02_capability.md` | 02 | Q3–Q5 | [ ] |", "02"),
        ("| `03_content.md` | 03 | Q6–Q8 | [ ] |", "03"),
    ):
        assert stage_row in result_text, f"stage {label} row should be unticked"
    assert "approved_stages: []" in result_text
    assert "capability drifted after content review" in result_text
    # exactly one loop-back row was added, from the highest stage sent back
    assert result_text.count("| 20") == 1
    assert "| 03 | 01 | capability drifted after content review | pending |" in result_text
