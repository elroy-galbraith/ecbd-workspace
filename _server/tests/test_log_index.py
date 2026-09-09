import subprocess
from pathlib import Path

from app.log_index import append_run, commit_log_index


def test_append_run_adds_a_row(tmp_repo: Path):
    log_path = tmp_repo / "worksheets" / "_index" / "log.md"
    before = log_path.read_text(encoding="utf-8")
    append_run(tmp_repo, "design-my-eval", "design", "A test eval", "2026-09-09")
    after = log_path.read_text(encoding="utf-8")
    assert after.startswith(before)
    assert "| design-my-eval | design | A test eval | 2026-09-09 | |" in after


def test_commit_log_index_commits_only_that_file(tmp_repo: Path):
    append_run(tmp_repo, "design-my-eval", "design", "A test eval", "2026-09-09")
    commit_log_index(tmp_repo, "design-my-eval")
    log_show = subprocess.run(
        ["git", "show", "--stat", "HEAD"], cwd=tmp_repo, check=True, capture_output=True, text=True,
    ).stdout
    assert "worksheets/_index/log.md" in log_show
    assert "design-my-eval" in subprocess.run(
        ["git", "log", "-1", "--format=%s"], cwd=tmp_repo, check=True, capture_output=True, text=True,
    ).stdout


def test_commit_log_index_does_not_sweep_in_unrelated_staged_changes(tmp_repo: Path):
    # Something else is already staged in the user's real working repo when
    # this fires -- commit_log_index must not commit it too.
    (tmp_repo / "unrelated.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "unrelated.txt"], cwd=tmp_repo, check=True, capture_output=True)

    append_run(tmp_repo, "design-my-eval", "design", "A test eval", "2026-09-09")
    commit_log_index(tmp_repo, "design-my-eval")

    log_show = subprocess.run(
        ["git", "show", "--stat", "HEAD"], cwd=tmp_repo, check=True, capture_output=True, text=True,
    ).stdout
    assert "worksheets/_index/log.md" in log_show
    assert "unrelated.txt" not in log_show

    # the unrelated file is still staged, untouched by this commit
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=tmp_repo, check=True, capture_output=True, text=True,
    ).stdout
    assert "unrelated.txt" in status
