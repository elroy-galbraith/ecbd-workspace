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


_APPROVED_STAGES_RE = re.compile(r"^(\s*approved_stages:\s*)\[(.*?)\](\s*)$", re.MULTILINE)


def _approved_stages_match(text: str) -> re.Match:
    match = _APPROVED_STAGES_RE.search(text)
    if match is None:
        raise RunMdError("'approved_stages:' line not found in RUN.md frontmatter")
    return match


def _parse_stage_list(inner: str) -> list[str]:
    inner = inner.strip()
    if not inner:
        return []
    stages = []
    for item in inner.split(","):
        item = item.strip()
        if len(item) >= 2 and item[0] == item[-1] and item[0] in "\"'":
            item = item[1:-1]
        stages.append(item)
    return stages


def _format_stage_list(stages: list[str]) -> str:
    return ", ".join(f'"{s}"' for s in stages)


def get_approved_stages(text: str) -> list[str]:
    match = _approved_stages_match(text)
    return _parse_stage_list(match.group(2))


def add_approved_stage(text: str, stage: str) -> str:
    match = _approved_stages_match(text)
    stages = _parse_stage_list(match.group(2))
    if stage not in stages:
        stages.append(stage)
    new_line = f"{match.group(1)}[{_format_stage_list(stages)}]{match.group(3)}"
    return text[: match.start()] + new_line + text[match.end() :]


def remove_approved_stages(text: str, stages: list[str]) -> str:
    match = _approved_stages_match(text)
    remaining = [s for s in _parse_stage_list(match.group(2)) if s not in stages]
    new_line = f"{match.group(1)}[{_format_stage_list(remaining)}]{match.group(3)}"
    return text[: match.start()] + new_line + text[match.end() :]


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
