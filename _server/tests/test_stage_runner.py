from pathlib import Path

import pytest

from app.model_client import ModelResponse, TextBlock, ToolUseBlock
from app.scope import load_stage_scope
from app.stage_runner import IterationLimitExceeded, StageRunner
from app.transcript import TranscriptStore
from tests.fakes import FakeModelClient


def _stage_01_scope(tmp_repo: Path):
    return load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=None,
    )


def test_text_only_turn_returns_immediately_and_records_transcript(tmp_repo: Path, tmp_path: Path):
    client = FakeModelClient([ModelResponse(content=[TextBlock(text="what should this measure?")], stop_reason="end_turn")])
    runner = StageRunner(
        scope=_stage_01_scope(tmp_repo),
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    reply = runner.send("I need an eval for summary faithfulness")

    assert reply == "what should this measure?"
    turns = TranscriptStore(tmp_path / "session.jsonl").read_all()
    assert turns[0]["role"] == "user"
    assert turns[1]["role"] == "assistant"


def test_create_run_tool_call_creates_the_run_and_binds_scope(tmp_repo: Path, tmp_path: Path):
    client = FakeModelClient([
        ModelResponse(
            content=[ToolUseBlock(id="call_1", name="create_run", input={"slug": "my-eval", "subject": "A test eval"})],
            stop_reason="tool_use",
        ),
        ModelResponse(content=[TextBlock(text="run created")], stop_reason="end_turn"),
    ])
    scope = _stage_01_scope(tmp_repo)
    runner = StageRunner(
        scope=scope,
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    runner.send("start a run")

    assert (tmp_repo / "worksheets" / "design-my-eval" / "RUN.md").exists()
    assert scope.run_root == tmp_repo / "worksheets" / "design-my-eval"


def test_write_file_then_mark_ready_for_review(tmp_repo: Path, tmp_path: Path):
    client = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "subj"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="write_file", input={"path": "01_intended-use.md", "content": "the use case"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c3", name="mark_ready_for_review", input={}) ], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="drafted, ready for your review")], stop_reason="end_turn"),
    ])
    scope = _stage_01_scope(tmp_repo)
    runner = StageRunner(
        scope=scope,
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    reply = runner.send("go")

    assert reply == "drafted, ready for your review"
    assert runner.ready_for_review is True
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    assert (run_root / "01_intended-use.md").read_text() == "the use case"
    assert "[x]" in (run_root / "RUN.md").read_text()


def test_tool_error_is_reported_back_to_the_model_not_raised(tmp_repo: Path, tmp_path: Path):
    client = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="write_file", input={"path": "not-declared.md", "content": "x"})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="understood, that path isn't available")], stop_reason="end_turn"),
    ])
    runner = StageRunner(
        scope=_stage_01_scope(tmp_repo),
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    reply = runner.send("go")

    assert reply == "understood, that path isn't available"
    turns = TranscriptStore(tmp_path / "session.jsonl").read_all()
    tool_result_turn = turns[2]
    assert tool_result_turn["content"][0]["is_error"] is True


def test_run_md_error_is_reported_back_to_the_model_not_raised(tmp_repo: Path, tmp_path: Path):
    # stage_number "99" has no row in RUN.md's stage table, so tick_stage()
    # raises RunMdError from inside _mark_ready_for_review. That must be
    # caught by _dispatch and reported to the model, not propagated out of
    # send() and crash the conversation loop.
    client = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "subj"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="mark_ready_for_review", input={})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="hit a snag marking ready")], stop_reason="end_turn"),
    ])
    runner = StageRunner(
        scope=_stage_01_scope(tmp_repo),
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="99",
    )

    reply = runner.send("go")

    assert reply == "hit a snag marking ready"
    assert runner.ready_for_review is False
    turns = TranscriptStore(tmp_path / "session.jsonl").read_all()
    tool_result_turn = turns[4]
    assert tool_result_turn["content"][0]["is_error"] is True


def test_unanticipated_exception_in_dispatch_is_reported_not_raised(tmp_repo: Path, tmp_path: Path):
    # write_file's input is missing "content", so _dispatch's
    # call.input["content"] lookup raises KeyError -- a type of exception
    # not in _dispatch's specific except clause. It must still be caught
    # and reported as a tool error, not escape send() and leave the
    # transcript ending in an unanswered tool_use block.
    client = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="write_file", input={"path": "01_intended-use.md"})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="hit an unexpected snag")], stop_reason="end_turn"),
    ])
    runner = StageRunner(
        scope=_stage_01_scope(tmp_repo),
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    reply = runner.send("go")

    assert reply == "hit an unexpected snag"
    turns = TranscriptStore(tmp_path / "session.jsonl").read_all()
    tool_result_turn = turns[2]
    assert tool_result_turn["content"][0]["is_error"] is True
    assert "content" in tool_result_turn["content"][0]["content"]


def test_runaway_tool_loop_raises_iteration_limit(tmp_repo: Path, tmp_path: Path):
    responses = [
        ModelResponse(content=[ToolUseBlock(id=f"c{i}", name="read_file", input={"path": "_shared/ecbd-framework.md"})], stop_reason="tool_use")
        for i in range(40)
    ]
    client = FakeModelClient(responses)
    runner = StageRunner(
        scope=_stage_01_scope(tmp_repo),
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    with pytest.raises(IterationLimitExceeded):
        runner.send("go")
