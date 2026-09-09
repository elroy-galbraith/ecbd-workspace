"""Session-start file snapshots, used to render a human-check diff without
ever touching git -- worksheet content is never committed (see
docs/decisions/2026-09-09-orchestration-backend.md)."""
from __future__ import annotations

import difflib
from pathlib import Path


class SnapshotStore:
    def __init__(self, snapshot_dir: Path):
        self.snapshot_dir = snapshot_dir

    def _snapshot_path(self, declared_path: str) -> Path:
        safe_name = declared_path.replace("/", "__")
        return self.snapshot_dir / f"{safe_name}.before"

    def capture(self, declared_path: str, current_content: str) -> None:
        snap_path = self._snapshot_path(declared_path)
        if snap_path.exists():
            return
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        snap_path.write_text(current_content, encoding="utf-8")

    def diff(self, declared_path: str, current_content: str) -> str:
        snap_path = self._snapshot_path(declared_path)
        before = snap_path.read_text(encoding="utf-8") if snap_path.exists() else ""
        return "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                current_content.splitlines(keepends=True),
                fromfile=f"{declared_path} (session start)",
                tofile=f"{declared_path} (current)",
            )
        )
