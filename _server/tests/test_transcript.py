from pathlib import Path

from app.transcript import TranscriptStore


def test_append_then_read_all_round_trips(tmp_path: Path):
    store = TranscriptStore(tmp_path / "session.jsonl")
    store.append({"role": "user", "content": [{"type": "text", "text": "hello"}]})
    store.append({"role": "assistant", "content": [{"type": "text", "text": "hi"}]})
    turns = store.read_all()
    assert turns == [
        {"role": "user", "content": [{"type": "text", "text": "hello"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "hi"}]},
    ]


def test_read_all_on_missing_file_returns_empty_list(tmp_path: Path):
    store = TranscriptStore(tmp_path / "nonexistent.jsonl")
    assert store.read_all() == []


def test_append_creates_parent_directories(tmp_path: Path):
    store = TranscriptStore(tmp_path / "nested" / "session.jsonl")
    store.append({"role": "user", "content": []})
    assert (tmp_path / "nested" / "session.jsonl").exists()
