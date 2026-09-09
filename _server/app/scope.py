from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .contract import Access, ContractError, StageContract, parse_contract


@dataclass
class StageScope:
    contract: StageContract
    repo_root: Path
    stage_dir: Path
    run_root: Path | None = None
    readable_files: dict[str, Path] = field(default_factory=dict)
    writable_files: dict[str, Path] = field(default_factory=dict)
    readable_dirs: dict[str, Path] = field(default_factory=dict)
    writable_dirs: dict[str, Path] = field(default_factory=dict)

    def bind_run_root(self, run_root: Path) -> None:
        """Called once create_run has produced the run folder, so
        run-relative paths declared in the contract become resolvable."""
        self.run_root = run_root
        self._rebuild()

    def _base_for(self, relative_to: str) -> Path | None:
        if relative_to == "repo":
            return self.repo_root
        if relative_to == "stage":
            return self.stage_dir
        return self.run_root

    def _rebuild(self) -> None:
        self.readable_files, self.writable_files = {}, {}
        self.readable_dirs, self.writable_dirs = {}, {}

        for spec in self.contract.inputs:
            base = self._base_for(spec.relative_to)
            if base is None:
                continue
            absolute = (base / spec.path).resolve()
            if spec.is_directory:
                self.readable_dirs[spec.path] = absolute
                if spec.access == Access.READ_WRITE:
                    self.writable_dirs[spec.path] = absolute
                continue
            if not absolute.exists():
                if spec.optional:
                    continue
                raise ContractError(f"required input missing: {spec.path}")
            self.readable_files[spec.path] = absolute
            if spec.access == Access.READ_WRITE:
                self.writable_files[spec.path] = absolute

        for out in self.contract.outputs:
            base = self._base_for(out.relative_to)
            if base is None:
                continue
            absolute = (base / out.path).resolve()
            if out.is_directory:
                self.writable_dirs[out.path] = absolute
                self.readable_dirs.setdefault(out.path, absolute)
            else:
                self.writable_files[out.path] = absolute
                self.readable_files.setdefault(out.path, absolute)

    def resolve_readable(self, path: str) -> Path:
        return self._resolve(path, self.readable_files, self.readable_dirs)

    def resolve_writable(self, path: str) -> Path:
        return self._resolve(path, self.writable_files, self.writable_dirs)

    @staticmethod
    def _resolve(path: str, files: dict[str, Path], dirs: dict[str, Path]) -> Path:
        if path in files:
            return files[path]
        for prefix, base_dir in dirs.items():
            if path != prefix and path.startswith(prefix):
                remainder = path[len(prefix):]
                if ".." in Path(remainder).parts or Path(remainder).is_absolute():
                    raise ContractError(f"'{path}' escapes its declared directory '{prefix}'")
                return (base_dir / remainder).resolve()
        raise ContractError(f"'{path}' is not declared in this stage's scope")


def load_stage_scope(
    contract_path: Path, repo_root: Path, run_root: Path | None = None
) -> StageScope:
    text = contract_path.read_text(encoding="utf-8")
    contract = parse_contract(text)
    if run_root is None and not contract.bootstrap:
        raise ContractError("run_root is required for a non-bootstrap stage")
    scope = StageScope(
        contract=contract,
        repo_root=repo_root,
        stage_dir=contract_path.parent,
        run_root=run_root,
    )
    scope._rebuild()
    return scope
