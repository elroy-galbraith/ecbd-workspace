"""Append a run to worksheets/_index/log.md and commit it -- the one place
this backend ever touches git, since that file (unlike a run folder) is
tracked. See docs/decisions/2026-09-09-orchestration-backend.md."""
from __future__ import annotations

import subprocess
from pathlib import Path


class LogIndexError(Exception):
    """Raised when git operations on the log index fail."""
    pass


def append_run(repo_root: Path, slug: str, mode: str, subject: str, opened: str) -> None:
    log_path = repo_root / "worksheets" / "_index" / "log.md"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    row = f"| {slug} | {mode} | {subject} | {opened} | |"
    lines.insert(_end_of_run_table(lines), row)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _end_of_run_table(lines: list[str]) -> int:
    """Index of the line just past the run table's last row. log.md carries a
    second table below it ('Changes to the factory'), so a row appended at
    end-of-file would land in that one instead."""
    header = next((i for i, line in enumerate(lines) if line.startswith("| Slug")), None)
    if header is None:
        raise LogIndexError(
            "worksheets/_index/log.md has no run table: no row starting '| Slug'"
        )
    index = header + 1
    while index < len(lines) and lines[index].startswith("|"):
        index += 1
    return index


def commit_log_index(repo_root: Path, slug: str) -> None:
    rel_path = "worksheets/_index/log.md"
    try:
        subprocess.run(["git", "add", rel_path], cwd=repo_root, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise LogIndexError(
            f"Failed to stage {rel_path}: {e.stderr.decode('utf-8', errors='replace')}"
        ) from e

    try:
        subprocess.run(
            ["git", "commit", "-m", f"Add {slug} to the run log", "--", rel_path],
            cwd=repo_root, check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        raise LogIndexError(
            f"Failed to commit {rel_path}: {e.stderr.decode('utf-8', errors='replace')}"
        ) from e
