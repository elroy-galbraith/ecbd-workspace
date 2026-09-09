# _server/tests/test_api.py
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.model_client import ModelResponse, TextBlock, ToolUseBlock
from tests.fakes import FakeModelClient


def test_full_stage_1_to_stage_2_flow_with_a_loop_back(tmp_repo: Path):
    client_stage_1 = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "A faithfulness eval"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="write_file", input={"path": "01_intended-use.md", "content": "the intended use, spelled out"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c3", name="mark_ready_for_review", input={})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="drafted, ready for review")], stop_reason="end_turn"),
    ])
    app = create_app(model_client=client_stage_1, repo_root=tmp_repo)
    api = TestClient(app)

    start = api.post("/runs/design/start", json={"brief": "I need a faithfulness eval"})
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    session = api.get(f"/sessions/{session_id}")
    assert session.status_code == 200
    assert len(session.json()["transcript"]) >= 2

    diff = api.get("/runs/design-my-eval/diff/01")
    assert diff.status_code == 200
    assert "+the intended use, spelled out" in diff.json()["diff"]

    approve = api.post("/runs/design-my-eval/stages/01/approve")
    assert approve.status_code == 200

    runs = api.get("/runs").json()
    assert any(r["slug"] == "design-my-eval" for r in runs)

    # Stage 2 becomes reachable now that stage 1 is approved.
    client_stage_2 = FakeModelClient([
        ModelResponse(content=[TextBlock(text="what capability does this eval target?")], stop_reason="end_turn"),
    ])
    app.dependency_overrides.clear()
    app2 = create_app(model_client=client_stage_2, repo_root=tmp_repo)
    api2 = TestClient(app2)
    stage_2_start = api2.post("/runs/design-my-eval/stages/02/start", json={"brief": "let's define the capability"})
    assert stage_2_start.status_code == 200

    # A rejection sends stage 2 back to stage 1 and records why.
    reject = api2.post(
        "/runs/design-my-eval/stages/02/reject",
        json={"target_stage": "01", "reason": "intended use was too vague"},
    )
    assert reject.status_code == 200
    run_md = (tmp_repo / "worksheets" / "design-my-eval" / "RUN.md").read_text()
    assert "intended use was too vague" in run_md


def test_start_stage_2_before_stage_1_is_approved_is_rejected(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.post("/runs/design-my-eval/stages/02/start", json={"brief": "go"})
    assert response.status_code == 404


def test_invalid_stage_on_start_is_rejected_cleanly(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.post("/runs/design-my-eval/stages/99/start", json={"brief": "go"})
    assert response.status_code == 404


def test_invalid_stage_on_approve_is_rejected_cleanly(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.post("/runs/design-my-eval/stages/99/approve")
    assert response.status_code == 404


def test_invalid_stage_on_reject_is_rejected_cleanly(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.post(
        "/runs/design-my-eval/stages/99/reject",
        json={"target_stage": "01", "reason": "n/a"},
    )
    assert response.status_code == 404


def test_invalid_stage_on_diff_is_rejected_cleanly(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.get("/runs/design-my-eval/diff/99")
    assert response.status_code == 404
