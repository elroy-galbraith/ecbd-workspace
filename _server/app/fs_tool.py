from __future__ import annotations

import difflib
from pathlib import Path

from .contract import ContractError
from .scope import StageScope

# Below this much overlap with what was there before, a write_file call reads
# as a full-document regeneration rather than a targeted change -- the case
# edit_file exists for. Chosen loose on purpose: this should only catch a
# near-total rewrite, never a real, human-approved restructuring.
_OVERWRITE_SIMILARITY_THRESHOLD = 0.5


class ScopeError(Exception):
    """Raised when a stage's model conversation asks for a path outside its
    declared scope, or an access level it doesn't hold."""


class ScopedFilesystemTool:
    """The only way a stage's model conversation may touch the filesystem.
    Every path is looked up against the stage's resolved StageScope --
    there is no path traversal surface, because an unrecognized or
    out-of-scope string simply raises rather than resolving to a real path.
    """

    def __init__(self, scope: StageScope):
        self.scope = scope
        # Paths this tool instance has itself written to, via either tool,
        # this session. A stage's first write_file to a given output is
        # replacing the template's placeholder scaffolding -- expected and
        # unguarded. Once this session has put real content in a file,
        # further write_file calls to it are the risky case: a full
        # regeneration standing in for what should be a targeted edit_file
        # change (e.g. "please revise the wording" after mark_ready_for_review).
        self._written_paths: set[Path] = set()

    def read_file(self, path: str) -> str:
        target = self._resolve_or_raise(self.scope.resolve_readable, path)
        if not target.exists():
            raise ScopeError(f"'{path}' does not exist")
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> None:
        target = self._resolve_or_raise(self.scope.resolve_writable, path)
        if self._would_change_approval(target, content):
            raise ScopeError(
                "approved_stages in RUN.md can only be changed by "
                "approve_stage/reject_stage, not by a model tool"
            )
        if target in self._written_paths and self._would_collapse_content(target, content):
            raise ScopeError(
                f"'{path}' already has content this session wrote -- use edit_file "
                "for a targeted change instead of rewriting the whole document"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._written_paths.add(target)

    def edit_file(self, path: str, old: str, new: str) -> None:
        target = self._resolve_or_raise(self.scope.resolve_writable, path)
        text = target.read_text(encoding="utf-8") if target.exists() else ""
        if old not in text:
            raise ScopeError(f"text to replace was not found in '{path}'")
        new_content = text.replace(old, new, 1)
        if self._would_change_approval(target, new_content):
            raise ScopeError(
                "approved_stages in RUN.md can only be changed by "
                "approve_stage/reject_stage, not by a model tool"
            )
        target.write_text(new_content, encoding="utf-8")
        self._written_paths.add(target)

    @staticmethod
    def _resolve_or_raise(resolver, path: str):
        try:
            return resolver(path)
        except ContractError as exc:
            raise ScopeError(str(exc)) from exc

    def _would_change_approval(self, target: Path, new_content: str) -> bool:
        """True if writing new_content to target would change the value of
        RUN.md's approved_stages: line. That line is a fact only
        approve_stage/reject_stage (human-invoked, via approval.py) may
        write -- never a model-exposed tool like write_file/edit_file."""
        if target.name != "RUN.md":
            return False
        from .run_md import approved_stages_would_change

        current_content = target.read_text(encoding="utf-8") if target.exists() else ""
        return approved_stages_would_change(current_content, new_content)

    def _would_collapse_content(self, target: Path, new_content: str) -> bool:
        """True if write_file would replace this session's own prior content
        for target with something that barely resembles it -- e.g. a full
        regeneration standing in for a one- or two-line fix. Only called for
        a path already in _written_paths, so target existing with real
        content is already established; a genuine rewrite the human asked
        for still gets through edit_file's precise, quote-what-you-change
        contract."""
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        ratio = difflib.SequenceMatcher(None, existing, new_content).ratio()
        return ratio < _OVERWRITE_SIMILARITY_THRESHOLD
