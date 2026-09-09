from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REAL_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    for rel in ("_shared", "_templates/design-run", "01-design"):
        shutil.copytree(REAL_REPO_ROOT / rel, repo / rel)
    (repo / "worksheets" / "_index").mkdir(parents=True)
    shutil.copy(
        REAL_REPO_ROOT / "worksheets" / "_index" / "log.md",
        repo / "worksheets" / "_index" / "log.md",
    )
    shutil.copy(
        REAL_REPO_ROOT / "worksheets" / "CONTEXT.md",
        repo / "worksheets" / "CONTEXT.md",
    )

    def run(*args: str) -> None:
        subprocess.run(args, cwd=repo, check=True, capture_output=True)

    run("git", "init")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test")
    run("git", "add", "-A")
    run("git", "commit", "-m", "initial")
    return repo
