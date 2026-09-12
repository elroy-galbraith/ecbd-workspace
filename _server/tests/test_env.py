import os
import subprocess
from pathlib import Path

from app.env import find_env_file, load_env


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _repo_with_a_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """A real main checkout plus a real linked worktree -- the layout this
    repo uses when a session runs under .claude/worktrees/."""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init")
    _git(main, "config", "user.email", "test@example.com")
    _git(main, "config", "user.name", "Test")
    (main / "README.md").write_text("x", encoding="utf-8")
    _git(main, "add", "-A")
    _git(main, "commit", "-m", "initial")
    worktree = tmp_path / "worktrees" / "side"
    _git(main, "worktree", "add", str(worktree), "-b", "side")
    return main, worktree


def test_finds_the_env_file_at_the_repo_root(tmp_path: Path):
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=k\n", encoding="utf-8")

    assert find_env_file(tmp_path) == tmp_path / ".env"


def test_finds_nothing_when_the_repo_root_has_no_env_file(tmp_path: Path):
    assert find_env_file(tmp_path) is None


def test_finds_the_main_checkouts_env_file_from_inside_a_worktree(tmp_path: Path):
    main, worktree = _repo_with_a_worktree(tmp_path)
    (main / ".env").write_text("ANTHROPIC_API_KEY=k\n", encoding="utf-8")

    found = find_env_file(worktree)

    assert found is not None
    assert found.resolve() == (main / ".env").resolve()


def test_prefers_the_worktrees_own_env_file_over_the_main_checkouts(tmp_path: Path):
    main, worktree = _repo_with_a_worktree(tmp_path)
    (main / ".env").write_text("ANTHROPIC_API_KEY=from-main\n", encoding="utf-8")
    (worktree / ".env").write_text("ANTHROPIC_API_KEY=from-worktree\n", encoding="utf-8")

    found = find_env_file(worktree)

    assert found is not None
    assert found.resolve() == (worktree / ".env").resolve()


def test_load_env_puts_the_files_values_in_the_environment(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-from-the-file\n", encoding="utf-8")

    loaded = load_env(tmp_path)

    assert loaded == tmp_path / ".env"
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-from-the-file"


def test_load_env_leaves_a_variable_already_in_the_environment_alone(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-the-shell")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-from-the-file\n", encoding="utf-8")

    load_env(tmp_path)

    assert os.environ["ANTHROPIC_API_KEY"] == "sk-from-the-shell"


def test_load_env_reports_nothing_loaded_when_there_is_no_env_file(tmp_path: Path):
    assert load_env(tmp_path) is None
