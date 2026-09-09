"""Append-only JSON-lines transcript for one stage session. Lives at
.sessions/<session-id>.jsonl at the repo root -- gitignored, and not
nested under a run folder, since a bootstrap session exists before its
run folder does."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TranscriptStore:
    def __init__(self, path: Path):
        self.path = path

    def append(self, turn: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(turn) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
