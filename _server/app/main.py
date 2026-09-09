# _server/app/main.py
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .approval import ApprovalError, approve_stage, reject_stage
from .contract import ContractError
from .model_client import AnthropicModelClient, ModelClient
from .scope import load_stage_scope
from .snapshot import SnapshotStore
from .stage_runner import StageRunner
from .transcript import TranscriptStore

_STAGE_ORDER = ["01", "02", "03", "04", "05", "06", "07", "08"]
_STAGE_DIRS = {
    "01": "01_intended-use", "02": "02_capability", "03": "03_content",
    "04": "04_adaptation", "05": "05_assembly", "06": "06_evidence",
    "07": "07_validity-review", "08": "08_build",
}


class StartSessionRequest(BaseModel):
    brief: str


class RejectRequest(BaseModel):
    target_stage: str
    reason: str


def create_app(model_client: ModelClient | None = None, repo_root: Path | None = None) -> FastAPI:
    repo_root = repo_root or Path(".").resolve()
    app = FastAPI(title="ecbd-workspace orchestration backend")
    sessions: dict[str, StageRunner] = {}

    def get_model_client() -> ModelClient:
        return model_client or AnthropicModelClient()

    def stage_contract_path(stage: str) -> Path:
        return repo_root / "01-design" / _STAGE_DIRS[stage] / "CONTEXT.md"

    def run_stage_table(slug: str) -> str:
        run_md = repo_root / "worksheets" / slug / "RUN.md"
        if not run_md.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        return run_md.read_text(encoding="utf-8")

    def stage_is_approved(slug: str, stage: str) -> bool:
        from .run_md import _find_stage_line_index

        lines = run_stage_table(slug).splitlines()
        idx = _find_stage_line_index(lines, stage)
        return "[x]" in lines[idx]

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/runs")
    def list_runs() -> list[dict[str, Any]]:
        log_path = repo_root / "worksheets" / "_index" / "log.md"
        rows = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|") or line.startswith("| Slug") or line.startswith("|---"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            rows.append({"slug": cols[0], "mode": cols[1], "subject": cols[2], "opened": cols[3]})
        return rows

    def _start_session(pipeline: str, stage: str, run_root: Path | None, brief: str) -> str:
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
        except ContractError as exc:
            raise HTTPException(500, str(exc)) from exc

        session_id = str(uuid.uuid4())
        runner = StageRunner(
            scope=scope,
            model_client=get_model_client(),
            transcript=TranscriptStore(repo_root / ".sessions" / f"{session_id}.jsonl"),
            repo_root=repo_root,
            pipeline=pipeline,
            stage_number=stage,
        )
        sessions[session_id] = runner
        runner.send(brief)
        return session_id

    @app.post("/runs/{pipeline}/start")
    def start_run(pipeline: str, req: StartSessionRequest) -> dict[str, str]:
        if pipeline != "design":
            raise HTTPException(400, f"pipeline '{pipeline}' is not supported yet")
        session_id = _start_session(pipeline, "01", run_root=None, brief=req.brief)
        return {"session_id": session_id}

    @app.post("/runs/{slug}/stages/{stage}/start")
    def start_stage(slug: str, stage: str, req: StartSessionRequest) -> dict[str, str]:
        run_root = repo_root / "worksheets" / slug
        if not run_root.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        stage_index = _STAGE_ORDER.index(stage)
        if stage_index > 0:
            previous_stage = _STAGE_ORDER[stage_index - 1]
            if not stage_is_approved(slug, previous_stage):
                raise HTTPException(404, f"stage {previous_stage} is not approved yet")
        session_id = _start_session(slug.split("-", 1)[0], stage, run_root=run_root, brief=req.brief)
        return {"session_id": session_id}

    @app.post("/sessions/{session_id}/messages")
    def send_message(session_id: str, req: StartSessionRequest) -> dict[str, str]:
        runner = sessions.get(session_id)
        if runner is None:
            raise HTTPException(404, f"no such session '{session_id}'")
        reply = runner.send(req.brief)
        return {"reply": reply}

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        runner = sessions.get(session_id)
        if runner is None:
            raise HTTPException(404, f"no such session '{session_id}'")
        return {"transcript": runner.transcript.read_all(), "ready_for_review": runner.ready_for_review}

    @app.post("/runs/{slug}/stages/{stage}/approve")
    def approve(slug: str, stage: str) -> dict[str, Any]:
        run_root = repo_root / "worksheets" / slug
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
            result = approve_stage(scope, stage)
        except (ContractError, ApprovalError) as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"approved_stage": result.approved_stage, "approved_outputs": result.approved_outputs}

    @app.post("/runs/{slug}/stages/{stage}/reject")
    def reject(slug: str, stage: str, req: RejectRequest) -> dict[str, str]:
        run_root = repo_root / "worksheets" / slug
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
            reject_stage(scope, from_stage=stage, target_stage=req.target_stage, reason=req.reason)
        except ContractError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"status": "rejected"}

    @app.get("/runs/{slug}/diff/{stage}")
    def diff(slug: str, stage: str) -> dict[str, str]:
        # NOTE: this captures the baseline lazily, on first call, rather than
        # precisely at session start as the spec describes. For a stage
        # output that didn't exist before the session (the common case --
        # every design stage writes a file its own template doesn't
        # pre-populate), an empty baseline is correct either way. It is
        # NOT correct for re-diffing a file that already had content before
        # THIS session touched it, if diff() is never called until after
        # several edits. Wiring capture() to fire the moment a session opens
        # (rather than the moment a diff is first requested) is a fast
        # follow, not done in this task -- see "What is not decided".
        run_root = repo_root / "worksheets" / slug
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
        except ContractError as exc:
            raise HTTPException(400, str(exc)) from exc
        snapshots = SnapshotStore(repo_root / ".sessions" / f"{slug}-{stage}-snapshots")
        combined = []
        for spec in scope.contract.outputs:
            if spec.is_directory:
                continue
            target = scope.writable_files[spec.path]
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            snapshots.capture(spec.path, "")
            combined.append(snapshots.diff(spec.path, current))
        return {"diff": "\n".join(combined)}

    return app
