from __future__ import annotations

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
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def edit_file(self, path: str, old: str, new: str) -> None:
        target = self._resolve_or_raise(self.scope.resolve_writable, path)
        text = target.read_text(encoding="utf-8") if target.exists() else ""
        if old not in text:
            raise ScopeError(f"text to replace was not found in '{path}'")
        target.write_text(text.replace(old, new, 1), encoding="utf-8")

    @staticmethod
    def _resolve_or_raise(resolver, path: str):
        try:
            return resolver(path)
        except ContractError as exc:
            raise ScopeError(str(exc)) from exc
