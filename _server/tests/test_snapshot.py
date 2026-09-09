from pathlib import Path

from app.snapshot import SnapshotStore


def test_diff_shows_no_change_before_any_edit(tmp_path: Path):
    store = SnapshotStore(tmp_path / "snapshots")
    store.capture("02_capability.md", "original content\n")
    diff = store.diff("02_capability.md", "original content\n")
    assert diff == ""


def test_diff_shows_added_lines(tmp_path: Path):
    store = SnapshotStore(tmp_path / "snapshots")
    store.capture("02_capability.md", "line one\n")
    diff = store.diff("02_capability.md", "line one\nline two\n")
    assert "+line two" in diff


def test_second_capture_does_not_overwrite_the_baseline(tmp_path: Path):
    store = SnapshotStore(tmp_path / "snapshots")
    store.capture("02_capability.md", "first version\n")
    store.capture("02_capability.md", "second version\n")  # should be ignored
    diff = store.diff("02_capability.md", "second version\n")
    assert "+second version" in diff
    assert "-first version" in diff


def test_diff_against_a_file_that_did_not_exist_at_session_start(tmp_path: Path):
    store = SnapshotStore(tmp_path / "snapshots")
    diff = store.diff("02_capability.md", "brand new content\n")
    assert "+brand new content" in diff
