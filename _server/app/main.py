# _server/app/main.py
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from .approval import ApprovalError, approve_stage, reject_stage
from .contract import ContractError
from .model_client import AnthropicModelClient, ModelClient
from .run_md import RunMdError, approved_stages_would_change, get_approved_stages, parse_run_md
from .scope import load_stage_scope
from .snapshot import SnapshotStore
from .stage_runner import StageRunner, TruncatedResponseError
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


class FileWriteRequest(BaseModel):
    content: str


def _resolve_run_file(run_root: Path, file_path: str) -> Path:
    target = (run_root / file_path).resolve()
    if not target.is_relative_to(run_root.resolve()):
        raise HTTPException(400, f"'{file_path}' escapes the run folder")
    return target


def _build_tree(directory: Path, root: Path) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for child in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if child.name.startswith("."):  # covers .sessions/ and any other dotfile
            continue
        rel_path = child.relative_to(root).as_posix()
        if child.is_dir():
            nodes.append(
                {"name": child.name, "path": rel_path, "is_dir": True, "children": _build_tree(child, root)}
            )
        else:
            nodes.append({"name": child.name, "path": rel_path, "is_dir": False, "children": None})
    return nodes


def _require_valid_stage(stage: str) -> None:
    if stage not in _STAGE_ORDER:
        raise HTTPException(404, f"no such stage '{stage}'")


def create_app(model_client: ModelClient | None = None, repo_root: Path | None = None) -> FastAPI:
    repo_root = repo_root or Path(__file__).resolve().parents[2]
    app = FastAPI(title="ecbd-workspace orchestration backend")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
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
        text = run_stage_table(slug)
        return stage in get_approved_stages(text)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/runs")
    def list_runs() -> list[dict[str, Any]]:
        # log.md holds more than one table -- 'Changes to the factory' has its
        # own, narrower columns. Read the run table and stop where it ends.
        log_path = repo_root / "worksheets" / "_index" / "log.md"
        rows = []
        in_run_table = False
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("| Slug"):
                in_run_table = True
                continue
            if not in_run_table:
                continue
            if not line.startswith("|"):
                break
            if line.startswith("|---"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            rows.append({"slug": cols[0], "mode": cols[1], "subject": cols[2], "opened": cols[3]})
        return rows

    @app.get("/runs/{slug}")
    def get_run(slug: str) -> dict[str, Any]:
        text = run_stage_table(slug)
        try:
            parsed = parse_run_md(text)
        except RunMdError as exc:
            raise HTTPException(500, str(exc)) from exc
        return {"slug": slug, **parsed}

    def _start_session(pipeline: str, stage: str, run_root: Path | None, brief: str) -> str:
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
        except ContractError as exc:
            logger.error(f"stage {stage} scope failed to load: {exc}")
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
        logger.info(f"session {session_id}: starting stage {stage} (pipeline={pipeline}, run_root={run_root})")
        try:
            runner.send(brief)
        except TruncatedResponseError as exc:
            logger.error(f"session {session_id}: {exc}")
            raise HTTPException(502, str(exc)) from exc
        logger.info(f"session {session_id}: stage {stage} responded, ready_for_review={runner.ready_for_review}")
        return session_id

    @app.post("/runs/{pipeline}/start")
    def start_run(pipeline: str, req: StartSessionRequest) -> dict[str, str]:
        logger.info(f"POST /runs/{pipeline}/start")
        if pipeline != "design":
            raise HTTPException(400, f"pipeline '{pipeline}' is not supported yet")
        session_id = _start_session(pipeline, "01", run_root=None, brief=req.brief)
        return {"session_id": session_id}

    @app.post("/runs/{slug}/stages/{stage}/start")
    def start_stage(slug: str, stage: str, req: StartSessionRequest) -> dict[str, str]:
        logger.info(f"POST /runs/{slug}/stages/{stage}/start")
        _require_valid_stage(stage)
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
        logger.info(f"POST /sessions/{session_id}/messages")
        runner = sessions.get(session_id)
        if runner is None:
            raise HTTPException(404, f"no such session '{session_id}'")
        try:
            reply = runner.send(req.brief)
        except TruncatedResponseError as exc:
            logger.error(f"session {session_id}: {exc}")
            raise HTTPException(502, str(exc)) from exc
        logger.info(f"session {session_id}: responded, ready_for_review={runner.ready_for_review}")
        return {"reply": reply}

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        runner = sessions.get(session_id)
        if runner is None:
            raise HTTPException(404, f"no such session '{session_id}'")
        return {"transcript": runner.transcript.read_all(), "ready_for_review": runner.ready_for_review}

    @app.post("/runs/{slug}/stages/{stage}/approve")
    def approve(slug: str, stage: str) -> dict[str, Any]:
        _require_valid_stage(stage)
        run_root = repo_root / "worksheets" / slug
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
            result = approve_stage(scope, stage)
        except (ContractError, ApprovalError) as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"approved_stage": result.approved_stage, "approved_outputs": result.approved_outputs}

    @app.post("/runs/{slug}/stages/{stage}/reject")
    def reject(slug: str, stage: str, req: RejectRequest) -> dict[str, str]:
        _require_valid_stage(stage)
        _require_valid_stage(req.target_stage)
        run_root = repo_root / "worksheets" / slug
        stage_index = _STAGE_ORDER.index(stage)
        target_index = _STAGE_ORDER.index(req.target_stage)
        stages_to_untick = _STAGE_ORDER[target_index : stage_index + 1]
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
            reject_stage(
                scope,
                stages_to_untick=stages_to_untick,
                target_stage=req.target_stage,
                reason=req.reason,
            )
        except ContractError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"status": "rejected"}

    @app.get("/runs/{slug}/diff/{stage}")
    def diff(slug: str, stage: str) -> dict[str, str]:
        _require_valid_stage(stage)
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

    @app.get("/runs/{slug}/files/{file_path:path}")
    def get_file(slug: str, file_path: str) -> dict[str, str]:
        run_root = repo_root / "worksheets" / slug
        if not run_root.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        target = _resolve_run_file(run_root, file_path)
        if not target.exists() or not target.is_file():
            raise HTTPException(404, f"'{file_path}' does not exist in run '{slug}'")
        return {"path": file_path, "content": target.read_text(encoding="utf-8")}

    @app.put("/runs/{slug}/files/{file_path:path}")
    def put_file(slug: str, file_path: str, req: FileWriteRequest) -> dict[str, str]:
        run_root = repo_root / "worksheets" / slug
        if not run_root.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        target = _resolve_run_file(run_root, file_path)
        if target.name == "RUN.md":
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            if approved_stages_would_change(current, req.content):
                raise HTTPException(
                    400,
                    "approved_stages in RUN.md can only be changed by approve/reject, not a direct file edit",
                )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(req.content, encoding="utf-8")
        return {"path": file_path, "content": req.content}

    @app.get("/runs/{slug}/tree")
    def get_tree(slug: str) -> dict[str, Any]:
        run_root = repo_root / "worksheets" / slug
        if not run_root.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        return {"tree": _build_tree(run_root, run_root)}

    return app


if __name__ == "__main__":
    import os

    import uvicorn

    from .env import load_env

    _repo_root = Path(__file__).resolve().parents[2]
    _env_file = load_env(_repo_root)
    if _env_file is not None:
        logger.info(f"env: read {_env_file}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning(
            "env: ANTHROPIC_API_KEY is not set. Reading runs will work; starting "
            "or continuing a stage will not. Put the key in "
            f"{_repo_root / '.env'} as ANTHROPIC_API_KEY=sk-ant-..."
        )
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
