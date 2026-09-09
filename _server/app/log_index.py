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
    text = log_path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    row = f"| {slug} | {mode} | {subject} | {opened} | |\n"
    log_path.write_text(text + row, encoding="utf-8")


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
            ["git", "commit", "-m", f"Add {slug} to the run log"],
            cwd=repo_root, check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        raise LogIndexError(
            f"Failed to commit {rel_path}: {e.stderr.decode('utf-8', errors='replace')}"
        ) from e
