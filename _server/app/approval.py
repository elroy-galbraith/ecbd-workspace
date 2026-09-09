"""Stage approval and rejection -- the human-check gate. Enforces that a
stage's declared outputs actually exist before the next stage becomes
reachable, and records loop-backs when a human sends work back to an
earlier stage. No git operation happens here; see
docs/decisions/2026-09-09-orchestration-backend.md."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .run_md import add_loop_back, tick_stage, untick_stage
from .scope import StageScope


class ApprovalError(Exception):
    pass


@dataclass
class ApprovalResult:
    approved_stage: str
    approved_outputs: list[str]


def _run_md_path(scope: StageScope):
    path = scope.writable_files.get("RUN.md") or scope.readable_files.get("RUN.md")
    if path is None:
        raise ApprovalError("RUN.md is not in this stage's scope")
    return path


def approve_stage(scope: StageScope, stage_number: str) -> ApprovalResult:
    missing = []
    for spec in scope.contract.outputs:
        if spec.is_directory:
            continue  # directory outputs may legitimately be empty
        target = scope.writable_files.get(spec.path)
        if target is None or not target.exists() or target.stat().st_size == 0:
            missing.append(spec.path)
    if missing:
        raise ApprovalError(f"cannot approve: outputs not written yet: {missing}")

    run_md_path = _run_md_path(scope)
    text = run_md_path.read_text(encoding="utf-8")
    run_md_path.write_text(tick_stage(text, stage_number), encoding="utf-8")

    return ApprovalResult(
        approved_stage=stage_number,
        approved_outputs=[spec.path for spec in scope.contract.outputs if not spec.is_directory],
    )


def reject_stage(scope: StageScope, from_stage: str, target_stage: str, reason: str) -> None:
    run_md_path = _run_md_path(scope)
    text = run_md_path.read_text(encoding="utf-8")
    text = untick_stage(text, from_stage)
    text = add_loop_back(
        text,
        date=date.today().isoformat(),
        from_stage=from_stage,
        back_to_stage=target_stage,
        forced_by=reason,
        what_changed="pending",
    )
    run_md_path.write_text(text, encoding="utf-8")
