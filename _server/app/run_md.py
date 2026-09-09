from __future__ import annotations

import re


class RunMdError(Exception):
    pass


def _find_stage_line_index(lines: list[str], stage: str) -> int:
    pattern = re.compile(rf"^\|\s*`[^`]+`\s*\|\s*{re.escape(stage)}\s*\|")
    for i, line in enumerate(lines):
        if pattern.match(line):
            return i
    raise RunMdError(f"stage '{stage}' not found in RUN.md stage table")


def tick_stage(text: str, stage: str) -> str:
    lines = text.splitlines(keepends=True)
    idx = _find_stage_line_index(lines, stage)
    lines[idx] = lines[idx].replace("[ ]", "[x]")
    return "".join(lines)


def untick_stage(text: str, stage: str) -> str:
    lines = text.splitlines(keepends=True)
    idx = _find_stage_line_index(lines, stage)
    lines[idx] = lines[idx].replace("[x]", "[ ]")
    return "".join(lines)


_LOOPBACK_HEADER = (
    "| Date | From stage | Back to stage | What forced it | What changed |\n"
    "|---|---|---|---|---|\n"
)


def add_loop_back(
    text: str, date: str, from_stage: str, back_to_stage: str, forced_by: str, what_changed: str
) -> str:
    if _LOOPBACK_HEADER not in text:
        raise RunMdError("loop-back table header not found in RUN.md")
    row = f"| {date} | {from_stage} | {back_to_stage} | {forced_by} | {what_changed} |\n"
    return text.replace(_LOOPBACK_HEADER, _LOOPBACK_HEADER + row, 1)
