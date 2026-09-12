"""Reads a .env file into the process environment at startup, so the
Anthropic SDK finds ANTHROPIC_API_KEY without it being set by hand in
every shell.

Two locations, in order: the repo root, and -- when the repo root is a git
worktree -- the main checkout it was created from. The second is what makes
a session under .claude/worktrees/ work without a copy of the key per
worktree. Nothing above those is searched: a stray .env further up the
filesystem is not this repo's.

A real environment variable always wins. The .env file fills gaps, it never
overrides what the shell already set.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def find_env_file(repo_root: Path) -> Path | None:
    """The .env this repo should use, or None if there isn't one."""
    for candidate in _candidate_env_files(repo_root):
        if candidate.is_file():
            return candidate
    return None


def load_env(repo_root: Path) -> Path | None:
    """Load the repo's .env into os.environ. Returns the file it read, or
    None if there was none to read."""
    env_file = find_env_file(repo_root)
    if env_file is None:
        return None
    load_dotenv(env_file, override=False)
    return env_file


def _candidate_env_files(repo_root: Path):
    yield repo_root / ".env"
    main_checkout = _main_checkout_of_worktree(repo_root)
    if main_checkout is not None:
        yield main_checkout / ".env"


def _main_checkout_of_worktree(repo_root: Path) -> Path | None:
    """In a linked worktree, `.git` is a file pointing at
    `<main checkout>/.git/worktrees/<name>`. In a normal checkout it is a
    directory, and there is no other checkout to look in."""
    dot_git = repo_root / ".git"
    if not dot_git.is_file():
        return None
    pointer = dot_git.read_text(encoding="utf-8").strip()
    if not pointer.startswith("gitdir:"):
        return None
    git_dir = Path(pointer.split(":", 1)[1].strip())
    for parent in git_dir.parents:
        if parent.name == ".git":
            return parent.parent
    return None
