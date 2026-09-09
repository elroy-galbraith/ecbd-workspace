from __future__ import annotations

from pathlib import Path

from .contract import ContractError
from .scope import StageScope


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
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

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
        from .run_md import RunMdError, get_approved_stages

        try:
            current_content = target.read_text(encoding="utf-8") if target.exists() else ""
            current = get_approved_stages(current_content)
        except RunMdError:
            current = None  # no approved_stages: line in the current content -- nothing to protect
        try:
            proposed = get_approved_stages(new_content)
        except RunMdError:
            proposed = None  # the edit would remove/corrupt the line entirely -- also protect against this
        return current != proposed
