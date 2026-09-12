"""The per-stage conversation loop: call the model, dispatch any tool_use
blocks against this stage's scoped tools, and stop at the first text-only
turn. Whether that turn is a clarifying question or "drafted, ready for
review" is for the human reading it to judge -- both are the same
stop-and-wait point in this loop."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from .contract import ContractError
from .create_run import CreateRunError, create_run
from .fs_tool import ScopedFilesystemTool, ScopeError
from .log_index import LogIndexError
from .model_client import ModelClient, ModelResponse, TextBlock, ToolUseBlock
from .run_md import RunMdError, tick_stage
from .scope import StageScope
from .transcript import TranscriptStore

MAX_TOOL_ITERATIONS = 30


class IterationLimitExceeded(Exception):
    pass


class TruncatedResponseError(Exception):
    pass


_BASE_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the content of a file declared in this stage's Inputs.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file declared in this stage's Outputs or a read-write Input.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace the first occurrence of old text with new text in a writable file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old": {"type": "string"},
                "new": {"type": "string"},
            },
            "required": ["path", "old", "new"],
        },
    },
    {
        "name": "mark_ready_for_review",
        "description": "Tick this stage's row in RUN.md: a draft exists and is ready for the human check.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

_CREATE_RUN_TOOL = {
    "name": "create_run",
    "description": "Create this run's folder from the pipeline's template. Usable once, before the run exists.",
    "input_schema": {
        "type": "object",
        "properties": {"slug": {"type": "string"}, "subject": {"type": "string"}},
        "required": ["slug", "subject"],
    },
}


@dataclass
class _ToolResult:
    tool_use_id: str
    content: str
    is_error: bool = False


class StageRunner:
    def __init__(
        self,
        scope: StageScope,
        model_client: ModelClient,
        transcript: TranscriptStore,
        repo_root: Path,
        pipeline: str,
        stage_number: str,
    ):
        self.scope = scope
        self.model_client = model_client
        self.transcript = transcript
        self.repo_root = repo_root
        self.pipeline = pipeline
        self.stage_number = stage_number
        self.fs_tool = ScopedFilesystemTool(scope)
        self.ready_for_review = False

    def _tools(self) -> list[dict[str, Any]]:
        tools = list(_BASE_TOOLS)
        if self.scope.contract.bootstrap and self.scope.run_root is None:
            tools.append(_CREATE_RUN_TOOL)
        return tools

    def _system_prompt(self) -> list[dict[str, Any]]:
        repo_refs = "\n\n".join(
            f"### {spec.path}\n{self.fs_tool.read_file(spec.path)}"
            for spec in self.scope.contract.inputs
            if spec.relative_to in ("repo", "stage") and spec.path in self.scope.readable_files
        )
        run_refs = "\n\n".join(
            f"### {spec.path}\n{self.fs_tool.read_file(spec.path)}"
            for spec in self.scope.contract.inputs
            if spec.relative_to == "run" and spec.path in self.scope.readable_files
        )
        static_text = f"{self.scope.contract.prose}\n\n## Reference material\n{repo_refs}"
        blocks: list[dict[str, Any]] = [
            {"type": "text", "text": static_text, "cache_control": {"type": "ephemeral"}}
        ]
        if run_refs:
            blocks.append({"type": "text", "text": f"## This run's files so far\n{run_refs}"})
        return blocks

    def _dispatch(self, call: ToolUseBlock) -> _ToolResult:
        logger.debug(f"dispatching tool {call.name}({call.input})")
        try:
            if call.name == "read_file":
                return _ToolResult(call.id, self.fs_tool.read_file(call.input["path"]))
            if call.name == "write_file":
                if self.ready_for_review:
                    return _ToolResult(
                        call.id,
                        "this stage was already marked ready for review; a human must respond before further edits",
                        is_error=True,
                    )
                self.fs_tool.write_file(call.input["path"], call.input["content"])
                return _ToolResult(call.id, f"wrote {call.input['path']}")
            if call.name == "edit_file":
                if self.ready_for_review:
                    return _ToolResult(
                        call.id,
                        "this stage was already marked ready for review; a human must respond before further edits",
                        is_error=True,
                    )
                self.fs_tool.edit_file(call.input["path"], call.input["old"], call.input["new"])
                return _ToolResult(call.id, f"edited {call.input['path']}")
            if call.name == "mark_ready_for_review":
                return self._mark_ready_for_review(call)
            if call.name == "create_run":
                return self._create_run(call)
            return _ToolResult(call.id, f"unknown tool '{call.name}'", is_error=True)
        except (ScopeError, ContractError, CreateRunError, RunMdError, LogIndexError) as exc:
            logger.warning(f"tool {call.name} rejected: {exc}")
            return _ToolResult(call.id, str(exc), is_error=True)
        except Exception as exc:
            # Backstop: an uncaught exception here would leave the transcript
            # ending in a tool_use block with no matching tool_result, which
            # every future send() would replay to the API and get rejected
            # for -- permanently breaking the session. Every failure in this
            # method has a defined recovery path (report it to the model as
            # a tool error), so a broad catch is correct here specifically.
            logger.exception(f"tool {call.name} raised unexpectedly")
            return _ToolResult(call.id, f"tool failed: {exc}", is_error=True)

    def _mark_ready_for_review(self, call: ToolUseBlock) -> _ToolResult:
        run_md_path = self.scope.writable_files.get("RUN.md") or self.scope.readable_files.get("RUN.md")
        if run_md_path is None:
            raise ScopeError("RUN.md is not in this stage's scope")
        text = run_md_path.read_text(encoding="utf-8")
        run_md_path.write_text(tick_stage(text, self.stage_number), encoding="utf-8")
        self.ready_for_review = True
        return _ToolResult(call.id, "marked ready for review")

    def _create_run(self, call: ToolUseBlock) -> _ToolResult:
        run_root = create_run(self.repo_root, self.pipeline, call.input["slug"], call.input["subject"])
        self.scope.bind_run_root(run_root)
        return _ToolResult(call.id, f"created run at {run_root}")

    def send(self, user_message: str | None) -> str:
        messages = [
            {"role": t["role"], "content": t["content"]} for t in self.transcript.read_all()
        ]
        if user_message is not None:
            entry = {"role": "user", "content": [{"type": "text", "text": user_message}]}
            self.transcript.append(entry)
            messages.append(entry)
            # A new human message means the human is reopening this stage
            # for further edits -- the write-freeze from a prior
            # mark_ready_for_review() no longer applies.
            self.ready_for_review = False

        for iteration in range(1, MAX_TOOL_ITERATIONS + 1):
            logger.info(f"stage {self.stage_number}: calling model (iteration {iteration}/{MAX_TOOL_ITERATIONS})")
            response = self.model_client.create(
                system=self._system_prompt(), messages=messages, tools=self._tools()
            )
            logger.info(f"stage {self.stage_number}: model responded, stop_reason={response.stop_reason}")
            assistant_entry = {"role": "assistant", "content": _blocks_to_dicts(response)}
            self.transcript.append(assistant_entry)

            if response.stop_reason == "max_tokens":
                raise TruncatedResponseError(
                    f"stage {self.stage_number} hit the token limit mid-turn -- "
                    "the model's response was cut off"
                )

            messages.append(assistant_entry)

            tool_calls = [b for b in response.content if isinstance(b, ToolUseBlock)]
            if not tool_calls:
                return "".join(b.text for b in response.content if isinstance(b, TextBlock))

            logger.info(f"stage {self.stage_number}: dispatching {len(tool_calls)} tool call(s): {[c.name for c in tool_calls]}")
            results = [self._dispatch(call) for call in tool_calls]
            tool_entry = {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": r.tool_use_id,
                        "content": r.content,
                        "is_error": r.is_error,
                    }
                    for r in results
                ],
            }
            self.transcript.append(tool_entry)
            messages.append(tool_entry)

        logger.error(f"stage {self.stage_number}: exceeded {MAX_TOOL_ITERATIONS} tool-call iterations")
        raise IterationLimitExceeded(
            f"stage {self.stage_number} exceeded {MAX_TOOL_ITERATIONS} tool-call iterations"
        )


def _blocks_to_dicts(response: ModelResponse) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for b in response.content:
        if isinstance(b, TextBlock):
            blocks.append({"type": "text", "text": b.text})
        elif isinstance(b, ToolUseBlock):
            blocks.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
    return blocks
