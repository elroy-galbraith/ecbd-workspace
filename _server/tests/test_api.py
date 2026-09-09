# _server/tests/test_api.py
from pathlib import Path

import pytest
from fastapi import HTTPException
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


def test_mark_ready_for_review_alone_does_not_unlock_stage_2(tmp_repo: Path):
    # The model ticks its own row via mark_ready_for_review, but nobody ever
    # calls POST .../approve. Stage 2 must stay locked -- this is the
    # negative case a "tick == approved" bug would let slip through.
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

    run_md = (tmp_repo / "worksheets" / "design-my-eval" / "RUN.md").read_text()
    assert "[x]" in run_md  # the model's own tick is present ...
    assert "approved_stages: []" in run_md  # ... but nothing approved it

    response = api.post("/runs/design-my-eval/stages/02/start", json={"brief": "go"})
    assert 400 <= response.status_code < 500


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


def test_get_run_returns_parsed_run_md(tmp_repo: Path):
    client_stage_1 = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "A faithfulness eval"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="write_file", input={"path": "01_intended-use.md", "content": "the intended use"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c3", name="mark_ready_for_review", input={})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="drafted")], stop_reason="end_turn"),
    ])
    app = create_app(model_client=client_stage_1, repo_root=tmp_repo)
    api = TestClient(app)
    api.post("/runs/design/start", json={"brief": "I need a faithfulness eval"})

    run = api.get("/runs/design-my-eval")
    assert run.status_code == 200
    body = run.json()
    assert body["slug"] == "design-my-eval"
    assert body["status"] == "intake"
    assert body["approved_stages"] == []
    stage_01 = next(s for s in body["stages"] if s["stage"] == "01")
    assert stage_01["done"] is True
    assert stage_01["file"] == "01_intended-use.md"
    assert body["loop_backs"] == []


def test_get_run_404_for_unknown_slug(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.get("/runs/design-nonexistent")
    assert response.status_code == 404


def test_get_file_returns_content(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)
    (run_root / "01_intended-use.md").write_text("hello", encoding="utf-8")

    response = api.get("/runs/design-my-eval/files/01_intended-use.md")
    assert response.status_code == 200
    assert response.json() == {"path": "01_intended-use.md", "content": "hello"}


def test_get_file_404_for_missing_file(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    (tmp_repo / "worksheets" / "design-my-eval").mkdir(parents=True)

    response = api.get("/runs/design-my-eval/files/nope.md")
    assert response.status_code == 404


def test_get_file_404_for_missing_run(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.get("/runs/design-nonexistent/files/nope.md")
    assert response.status_code == 404


def test_put_file_writes_content(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)

    response = api.put("/runs/design-my-eval/files/01_intended-use.md", json={"content": "edited by hand"})
    assert response.status_code == 200
    assert response.json() == {"path": "01_intended-use.md", "content": "edited by hand"}
    assert (run_root / "01_intended-use.md").read_text(encoding="utf-8") == "edited by hand"


def test_put_file_rejects_changing_approved_stages(tmp_repo: Path):
    client_stage_1 = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "A faithfulness eval"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="write_file", input={"path": "01_intended-use.md", "content": "the intended use"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c3", name="mark_ready_for_review", input={})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="drafted")], stop_reason="end_turn"),
    ])
    app = create_app(model_client=client_stage_1, repo_root=tmp_repo)
    api = TestClient(app)
    api.post("/runs/design/start", json={"brief": "I need a faithfulness eval"})

    run_md_path = tmp_repo / "worksheets" / "design-my-eval" / "RUN.md"
    tampered = run_md_path.read_text(encoding="utf-8").replace("approved_stages: []", 'approved_stages: ["01"]')

    response = api.put("/runs/design-my-eval/files/RUN.md", json={"content": tampered})
    assert response.status_code == 400
    assert "approved_stages" in run_md_path.read_text(encoding="utf-8")
    assert '["01"]' not in run_md_path.read_text(encoding="utf-8")


def test_resolve_run_file_rejects_path_traversal(tmp_repo: Path):
    from app.main import _resolve_run_file

    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)
    with pytest.raises(HTTPException):
        _resolve_run_file(run_root, "../../CLAUDE.md")


def test_cors_allows_the_vite_dev_origin(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.get("/runs", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
