from __future__ import annotations

import re
import yaml


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


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        raise RunMdError("RUN.md is missing a frontmatter block")
    end = text.find("\n---", 4)
    if end == -1:
        raise RunMdError("RUN.md frontmatter block is not terminated")
    return yaml.safe_load(text[4:end]) or {}


_STAGE_ROW_RE = re.compile(
    # The "Questions" column is design/audit-only (measure-run tables are
    # `| File | Stage | Done |`, three columns) -- so it's optional here.
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*(?:([^|]*?)\|\s*)?\[([ xX])\]\s*\|\s*$",
    re.MULTILINE,
)


def parse_stage_table(text: str) -> list[dict]:
    return [
        {
            "file": m.group(1),
            "stage": m.group(2),
            "questions": (m.group(3) or "").strip(),
            "done": m.group(4).lower() == "x",
        }
        for m in _STAGE_ROW_RE.finditer(text)
    ]


_LOOPBACK_ROW_RE = re.compile(
    r"^\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*$",
    re.MULTILINE,
)


def parse_loop_backs(text: str) -> list[dict]:
    idx = text.find(_LOOPBACK_HEADER)
    if idx == -1:
        return []
    after = text[idx + len(_LOOPBACK_HEADER):]
    return [
        {
            "date": cols[0], "from_stage": cols[1], "back_to_stage": cols[2],
            "forced_by": cols[3], "what_changed": cols[4],
        }
        for m in _LOOPBACK_ROW_RE.finditer(after)
        for cols in [[g.strip() for g in m.groups()]]
    ]


def parse_run_md(text: str) -> dict:
    """Read-only summary of a RUN.md, for any pipeline. `approved_stages` is a
    design-pipeline concept (only its template carries the frontmatter line,
    and only approve_stage/reject_stage may write it -- see
    approved_stages_would_change); audit and measure runs never have it, so
    this defaults to [] for them rather than raising, the same way
    approved_stages_would_change already treats a missing line as distinct
    from an empty list."""
    frontmatter = parse_frontmatter(text)
    try:
        approved_stages = get_approved_stages(text)
    except RunMdError:
        approved_stages = []
    return {
        "mode": frontmatter.get("mode"),
        "status": frontmatter.get("status"),
        "opened": frontmatter.get("opened"),
        "closed": frontmatter.get("closed"),
        "approved_stages": approved_stages,
        "stages": parse_stage_table(text),
        "loop_backs": parse_loop_backs(text),
    }


def approved_stages_would_change(current_content: str, new_content: str) -> bool:
    """True if writing new_content would change the parsed approved_stages
    list relative to current_content. Shared by ScopedFilesystemTool (blocks
    model-tool writes to RUN.md) and the file-edit API (blocks direct human
    writes) so both enforce the same invariant: approved_stages changes only
    through approve_stage/reject_stage."""
    try:
        current = get_approved_stages(current_content)
    except RunMdError:
        current = None
    try:
        proposed = get_approved_stages(new_content)
    except RunMdError:
        proposed = None
    return current != proposed


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
