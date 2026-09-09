# Orchestration Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the backend that lets a web UI drive the `01-design` pipeline the way Claude Code drives it today — reading a stage's contract, running a scoped conversation against the Anthropic API, and enforcing the human-check gate between stages — without a terminal.

**Architecture:** Five units (Contract Loader, Scoped Filesystem Tool, Stage Runner, run-lifecycle helpers, Stage Session API) operating directly on this repo's working tree. No database; `RUN.md` and the stage output files are the only state. No git commits touch worksheet content — the only commit this backend ever makes is the one-line append to the tracked `worksheets/_index/log.md`. Runs entirely on `127.0.0.1`; no auth.

**Tech Stack:** Python 3.11+, FastAPI + uvicorn, the `anthropic` SDK, PyYAML, pytest, httpx (for FastAPI's `TestClient`).

**Spec:** [docs/decisions/2026-09-09-orchestration-backend.md](../../decisions/2026-09-09-orchestration-backend.md) — read it alongside this plan; the plan argues from it and doesn't restate the "why."

**Scope of this plan:** only the `01-design` pipeline (8 stages). `02-audit` and `03-measure` need the same frontmatter treatment later but are out of scope here — see "What is not decided" in the spec. SSE streaming for `/sessions/:id/messages` is deferred; this plan implements a synchronous JSON response for that endpoint (the orchestration logic underneath is identical either way — streaming is a transport-layer follow-on, not part of what this plan proves out).

## Global Constraints

- Bind the FastAPI app to `127.0.0.1` only — never `0.0.0.0`. (spec: Decision, API surface)
- No code path may write to git inside a `worksheets/<slug>/` folder. The only git operation this backend ever performs is committing `worksheets/_index/log.md`. (spec: Decision)
- Every filesystem access the model makes must go through `ScopedFilesystemTool`, resolved from a stage's parsed contract — never a raw `open()`/`Path.read_text()` call reachable from a tool dispatch. (spec: Tool scoping)
- A stage contract has three possible path bases — `repo` (repo root), `run` (the run folder, unresolved until it exists), `stage` (the `CONTEXT.md`'s own directory, for files like `01-design/03_content/references/item-design.md`). A declared path ending in `/` is a directory scope (prefix match); anything else is an exact file match.
- Transcripts live at `.sessions/<session-id>.jsonl` at the repo root (add `.sessions/` to `.gitignore` in Task 1) — never nested under a run folder, since a bootstrap session exists before its run folder does.
- New backend code lives under `_server/`, matching this workspace's convention that underscore-prefixed top-level folders are infrastructure (`_shared/`, `_templates/`, `_tools/`), not pipeline content.

---

## Task 1: Project scaffold + health check

**Files:**
- Create: `_server/CONTEXT.md`
- Create: `_server/requirements.txt`
- Create: `_server/app/__init__.py`
- Create: `_server/app/main.py`
- Create: `_server/tests/__init__.py`
- Create: `_server/tests/test_health.py`
- Modify: `.gitignore` (add `.sessions/` and `_server/.venv/`)

**Interfaces:**
- Produces: `create_app() -> FastAPI` in `_server/app/main.py`, with one route `GET /health` returning `{"status": "ok"}`. Later tasks add routes and dependencies to this same factory function.

- [ ] **Step 1: Write the failing test**

```python
# _server/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd _server && python -m pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'` (module doesn't exist yet)

- [ ] **Step 3: Write the scaffold**

```
# _server/requirements.txt
fastapi>=0.110
uvicorn>=0.29
anthropic>=0.40
pyyaml>=6.0
pytest>=8.0
httpx>=0.27
```

```markdown
# _server/CONTEXT.md
The orchestration backend for the web-app version of this workspace. Not
part of any pipeline run — factory, like `_tools/`, not product.

Read `docs/decisions/2026-09-09-orchestration-backend.md` before touching
this folder; it explains the design this code implements, including two
choices that aren't obvious from the code alone: worksheet content is
never committed to git, and the server binds to localhost only.

Run tests from this directory: `python -m pytest tests/`.
```

```python
# _server/app/__init__.py
```

```python
# _server/app/main.py
from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="ecbd-workspace orchestration backend")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
```

Add to `.gitignore`:
```
# Orchestration backend: session transcripts, never committed
.sessions/
_server/.venv/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd _server && python -m pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _server/ .gitignore
git commit -m "Scaffold orchestration backend with a health check"
```

---

## Task 2: Contract Loader & StageScope

**Files:**
- Create: `_server/app/contract.py`
- Create: `_server/app/scope.py`
- Test: `_server/tests/test_contract.py`
- Test: `_server/tests/test_scope.py`

**Interfaces:**
- Produces (`contract.py`): `ContractError(Exception)`, `Access(str, Enum)` with `READ`/`READ_WRITE`, `InputSpec(path, relative_to, access, optional=False)` with `.is_directory` property, `OutputSpec(path, relative_to="run")` with `.is_directory` property, `StageContract(bootstrap, inputs, outputs, prose)`, `parse_contract(text: str) -> StageContract`.
- Produces (`scope.py`): `StageScope` dataclass with `.readable_files`, `.writable_files`, `.readable_dirs`, `.writable_dirs` (all `dict[str, Path]`), `.bind_run_root(run_root: Path) -> None`, `.resolve_readable(path: str) -> Path`, `.resolve_writable(path: str) -> Path` (both raise `ContractError` if `path` isn't in scope). `load_stage_scope(contract_path: Path, repo_root: Path, run_root: Path | None = None) -> StageScope`.

- [ ] **Step 1: Write the failing tests**

```python
# _server/tests/test_contract.py
import pytest

from app.contract import Access, ContractError, parse_contract

SAMPLE = """---
bootstrap: true
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 01_intended-use.md
    relative_to: run
---
# 01_intended-use

Some prose.
"""


def test_parses_bootstrap_flag_and_inputs():
    contract = parse_contract(SAMPLE)
    assert contract.bootstrap is True
    assert len(contract.inputs) == 3
    run_md = contract.inputs[0]
    assert run_md.path == "RUN.md"
    assert run_md.relative_to == "run"
    assert run_md.access == Access.READ_WRITE
    assert run_md.optional is False
    house = contract.inputs[2]
    assert house.optional is True


def test_parses_outputs_and_prose():
    contract = parse_contract(SAMPLE)
    assert contract.outputs[0].path == "01_intended-use.md"
    assert "# 01_intended-use" in contract.prose
    assert "---" not in contract.prose.split("\n")[0]


def test_directory_paths_are_detected():
    contract = parse_contract(SAMPLE.replace(
        "  - path: 01_intended-use.md\n    relative_to: run",
        "  - path: build/items/\n    relative_to: run",
    ))
    assert contract.outputs[0].is_directory is True


def test_missing_frontmatter_raises():
    with pytest.raises(ContractError):
        parse_contract("# no frontmatter here\n")


def test_unterminated_frontmatter_raises():
    with pytest.raises(ContractError):
        parse_contract("---\nbootstrap: true\n# never closed\n")
```

```python
# _server/tests/test_scope.py
from pathlib import Path

import pytest

from app.contract import ContractError
from app.scope import StageScope, load_stage_scope

CONTRACT = """---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 01_intended-use.md
    relative_to: run
    access: read
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
  - path: references/item-design.md
    relative_to: stage
    access: read
outputs:
  - path: 02_capability.md
    relative_to: run
  - path: build/items/
    relative_to: run
---
prose
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "_shared").mkdir()
    (tmp_path / "_shared" / "ecbd-framework.md").write_text("framework")
    stage_dir = tmp_path / "01-design" / "02_capability"
    stage_dir.mkdir(parents=True)
    (stage_dir / "CONTEXT.md").write_text(CONTRACT)
    (stage_dir / "references").mkdir()
    (stage_dir / "references" / "item-design.md").write_text("item design notes")
    run_root = tmp_path / "worksheets" / "design-test"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("run state")
    (run_root / "01_intended-use.md").write_text("intended use")
    return tmp_path


def test_resolves_all_three_bases(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)

    assert scope.resolve_readable("RUN.md") == (run_root / "RUN.md").resolve()
    assert scope.resolve_readable("_shared/ecbd-framework.md") == (repo / "_shared" / "ecbd-framework.md").resolve()
    assert scope.resolve_readable("references/item-design.md") == (
        repo / "01-design" / "02_capability" / "references" / "item-design.md"
    ).resolve()


def test_optional_missing_input_is_silently_dropped(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    with pytest.raises(ContractError):
        scope.resolve_readable("_shared/house-context.md")


def test_required_missing_input_raises(repo: Path):
    (repo / "worksheets" / "design-test" / "01_intended-use.md").unlink()
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    with pytest.raises(ContractError):
        load_stage_scope(contract_path, repo_root=repo, run_root=run_root)


def test_read_write_access_makes_a_path_writable(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    assert scope.resolve_writable("RUN.md") == (run_root / "RUN.md").resolve()
    with pytest.raises(ContractError):
        scope.resolve_writable("_shared/ecbd-framework.md")


def test_declared_output_is_writable_even_though_not_yet_created(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    assert scope.resolve_writable("02_capability.md") == (run_root / "02_capability.md").resolve()


def test_directory_output_accepts_any_file_beneath_it(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    assert scope.resolve_writable("build/items/item-001.json") == (
        run_root / "build" / "items" / "item-001.json"
    ).resolve()


def test_directory_traversal_out_of_a_declared_directory_is_rejected(repo: Path):
    contract_path = repo / "01-design" / "02_capability" / "CONTEXT.md"
    run_root = repo / "worksheets" / "design-test"
    scope = load_stage_scope(contract_path, repo_root=repo, run_root=run_root)
    with pytest.raises(ContractError):
        scope.resolve_writable("build/items/../../secrets.md")


def test_bootstrap_stage_defers_run_relative_paths_until_bound(tmp_path: Path):
    (tmp_path / "_shared").mkdir()
    (tmp_path / "_shared" / "ecbd-framework.md").write_text("framework")
    stage_dir = tmp_path / "01-design" / "01_intended-use"
    stage_dir.mkdir(parents=True)
    (stage_dir / "CONTEXT.md").write_text("""---
bootstrap: true
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
outputs:
  - path: 01_intended-use.md
    relative_to: run
---
prose
""")
    scope = load_stage_scope(stage_dir / "CONTEXT.md", repo_root=tmp_path, run_root=None)
    with pytest.raises(ContractError):
        scope.resolve_readable("RUN.md")

    run_root = tmp_path / "worksheets" / "design-test"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("run state")
    scope.bind_run_root(run_root)
    assert scope.resolve_readable("RUN.md") == (run_root / "RUN.md").resolve()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd _server && python -m pytest tests/test_contract.py tests/test_scope.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.contract'`

- [ ] **Step 3: Implement**

```python
# _server/app/contract.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import yaml

VALID_BASES = {"repo", "run", "stage"}


class ContractError(Exception):
    """Raised when a stage contract is missing, malformed, or violated."""


class Access(str, Enum):
    READ = "read"
    READ_WRITE = "read-write"


@dataclass(frozen=True)
class InputSpec:
    path: str
    relative_to: str
    access: Access
    optional: bool = False

    @property
    def is_directory(self) -> bool:
        return self.path.endswith("/")


@dataclass(frozen=True)
class OutputSpec:
    path: str
    relative_to: str = "run"

    @property
    def is_directory(self) -> bool:
        return self.path.endswith("/")


@dataclass(frozen=True)
class StageContract:
    bootstrap: bool
    inputs: tuple[InputSpec, ...]
    outputs: tuple[OutputSpec, ...]
    prose: str


def _check_base(relative_to: str, path: str) -> None:
    if relative_to not in VALID_BASES:
        raise ContractError(
            f"invalid relative_to '{relative_to}' for '{path}' "
            f"(must be one of {sorted(VALID_BASES)})"
        )


def parse_contract(text: str) -> StageContract:
    if not text.startswith("---\n"):
        raise ContractError("CONTEXT.md is missing a frontmatter block")
    end = text.find("\n---", 4)
    if end == -1:
        raise ContractError("CONTEXT.md frontmatter block is not terminated")
    front_matter = text[4:end]
    prose = text[end + 4:].lstrip("\n")

    data = yaml.safe_load(front_matter) or {}
    if "inputs" not in data:
        raise ContractError("contract frontmatter is missing 'inputs'")
    if "outputs" not in data:
        raise ContractError("contract frontmatter is missing 'outputs'")

    inputs = []
    for item in data["inputs"]:
        _check_base(item["relative_to"], item["path"])
        inputs.append(
            InputSpec(
                path=item["path"],
                relative_to=item["relative_to"],
                access=Access(item["access"]),
                optional=item.get("optional", False),
            )
        )

    outputs = []
    for item in data["outputs"]:
        relative_to = item.get("relative_to", "run")
        _check_base(relative_to, item["path"])
        outputs.append(OutputSpec(path=item["path"], relative_to=relative_to))

    return StageContract(
        bootstrap=bool(data.get("bootstrap", False)),
        inputs=tuple(inputs),
        outputs=tuple(outputs),
        prose=prose,
    )
```

```python
# _server/app/scope.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_contract.py tests/test_scope.py -v`
Expected: PASS (all cases)

- [ ] **Step 5: Commit**

```bash
git add _server/app/contract.py _server/app/scope.py _server/tests/test_contract.py _server/tests/test_scope.py
git commit -m "Add contract parsing and stage scope resolution"
```

---

## Task 3: Add frontmatter to the 8 `01-design` stage contracts

**Files:**
- Modify: `01-design/01_intended-use/CONTEXT.md`
- Modify: `01-design/02_capability/CONTEXT.md`
- Modify: `01-design/03_content/CONTEXT.md`
- Modify: `01-design/04_adaptation/CONTEXT.md`
- Modify: `01-design/05_assembly/CONTEXT.md`
- Modify: `01-design/06_evidence/CONTEXT.md`
- Modify: `01-design/07_validity-review/CONTEXT.md`
- Modify: `01-design/08_build/CONTEXT.md`
- Test: `_server/tests/test_real_contracts.py`

**Interfaces:**
- Consumes: `app.contract.parse_contract`, `app.scope.load_stage_scope` (Task 2).
- No new interfaces produced — this task makes the loader from Task 2 work against the actual repo, and is the contract-lint test the spec calls for.

Each `CONTEXT.md` gets a frontmatter block **prepended**, before its existing `# ` heading. Nothing in the existing prose changes.

- [ ] **Step 1: Write the failing test**

```python
# _server/tests/test_real_contracts.py
from pathlib import Path

import pytest

from app.contract import parse_contract
from app.scope import load_stage_scope

REPO_ROOT = Path(__file__).resolve().parents[2]

STAGES = [
    "01_intended-use", "02_capability", "03_content", "04_adaptation",
    "05_assembly", "06_evidence", "07_validity-review", "08_build",
]


@pytest.mark.parametrize("stage", STAGES)
def test_every_design_stage_contract_has_valid_frontmatter(stage: str):
    contract_path = REPO_ROOT / "01-design" / stage / "CONTEXT.md"
    text = contract_path.read_text(encoding="utf-8")
    contract = parse_contract(text)  # raises ContractError if malformed
    assert contract.outputs, f"{stage} declares no outputs"


def test_stage_01_is_the_only_bootstrap_stage():
    for stage in STAGES:
        contract_path = REPO_ROOT / "01-design" / stage / "CONTEXT.md"
        contract = parse_contract(contract_path.read_text(encoding="utf-8"))
        assert contract.bootstrap == (stage == "01_intended-use"), stage


def test_stage_02_scope_resolves_against_a_fabricated_run(tmp_path: Path):
    run_root = tmp_path / "worksheets" / "design-fixture"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("state")
    (run_root / "01_intended-use.md").write_text("intended use")
    scope = load_stage_scope(
        REPO_ROOT / "01-design" / "02_capability" / "CONTEXT.md",
        repo_root=REPO_ROOT,
        run_root=run_root,
    )
    assert scope.resolve_readable("_shared/capability-conventions.md").exists()
    assert scope.resolve_writable("02_capability.md") == (run_root / "02_capability.md").resolve()


def test_stage_03_has_a_stage_relative_reference_and_a_directory_output(tmp_path: Path):
    run_root = tmp_path / "worksheets" / "design-fixture"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("state")
    (run_root / "02_capability.md").write_text("capabilities")
    scope = load_stage_scope(
        REPO_ROOT / "01-design" / "03_content" / "CONTEXT.md",
        repo_root=REPO_ROOT,
        run_root=run_root,
    )
    assert scope.resolve_readable("references/item-design.md").exists()
    assert scope.resolve_writable("build/items/example.json") == (
        run_root / "build" / "items" / "example.json"
    ).resolve()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd _server && python -m pytest tests/test_real_contracts.py -v`
Expected: FAIL — `ContractError: CONTEXT.md is missing a frontmatter block` for every stage

- [ ] **Step 3: Add frontmatter to each stage contract**

Prepend to `01-design/01_intended-use/CONTEXT.md`:
```yaml
---
bootstrap: true
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: worksheets/_index/log.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 01_intended-use.md
    relative_to: run
---
```

Prepend to `01-design/02_capability/CONTEXT.md`:
```yaml
---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 01_intended-use.md
    relative_to: run
    access: read
  - path: _shared/capability-conventions.md
    relative_to: repo
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: _shared/validity-evidence.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 02_capability.md
    relative_to: run
---
```

Prepend to `01-design/03_content/CONTEXT.md`:
```yaml
---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 02_capability.md
    relative_to: run
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: _shared/validity-evidence.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
  - path: references/item-design.md
    relative_to: stage
    access: read
outputs:
  - path: 03_content.md
    relative_to: run
  - path: build/items/
    relative_to: run
---
```

Prepend to `01-design/04_adaptation/CONTEXT.md`:
```yaml
---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 03_content.md
    relative_to: run
    access: read
  - path: 02_capability.md
    relative_to: run
    access: read
  - path: 01_intended-use.md
    relative_to: run
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: _shared/validity-evidence.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 04_adaptation.md
    relative_to: run
  - path: build/adaptation/
    relative_to: run
---
```

Prepend to `01-design/05_assembly/CONTEXT.md`:
```yaml
---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 03_content.md
    relative_to: run
    access: read
  - path: 02_capability.md
    relative_to: run
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: _shared/validity-evidence.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 05_assembly.md
    relative_to: run
  - path: build/items/
    relative_to: run
---
```

Prepend to `01-design/06_evidence/CONTEXT.md`:
```yaml
---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 04_adaptation.md
    relative_to: run
    access: read
  - path: 02_capability.md
    relative_to: run
    access: read
  - path: 05_assembly.md
    relative_to: run
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: _shared/validity-evidence.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 06_evidence.md
    relative_to: run
  - path: build/scoring/
    relative_to: run
---
```

Prepend to `01-design/07_validity-review/CONTEXT.md`:
```yaml
---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 01_intended-use.md
    relative_to: run
    access: read
  - path: 02_capability.md
    relative_to: run
    access: read
  - path: 03_content.md
    relative_to: run
    access: read
  - path: 04_adaptation.md
    relative_to: run
    access: read
  - path: 05_assembly.md
    relative_to: run
    access: read
  - path: 06_evidence.md
    relative_to: run
    access: read
  - path: _shared/failure-modes.md
    relative_to: repo
    access: read
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
  - path: _shared/validity-evidence.md
    relative_to: repo
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 07_validity-register.md
    relative_to: run
---
```

Prepend to `01-design/08_build/CONTEXT.md`:
```yaml
---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 03_content.md
    relative_to: run
    access: read
  - path: 04_adaptation.md
    relative_to: run
    access: read
  - path: 05_assembly.md
    relative_to: run
    access: read
  - path: 06_evidence.md
    relative_to: run
    access: read
  - path: 07_validity-register.md
    relative_to: run
    access: read
  - path: 02_capability.md
    relative_to: run
    access: read
  - path: build/
    relative_to: run
    access: read-write
  - path: references/build-contract.md
    relative_to: stage
    access: read
  - path: _shared/openeval-schema.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: build/
    relative_to: run
---
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_real_contracts.py -v`
Expected: PASS for all 8 stages

- [ ] **Step 5: Commit**

```bash
git add 01-design/ _server/tests/test_real_contracts.py
git commit -m "Add machine-readable frontmatter to the 01-design stage contracts"
```

---

## Task 4: Scoped Filesystem Tool

**Files:**
- Create: `_server/app/fs_tool.py`
- Test: `_server/tests/test_fs_tool.py`

**Interfaces:**
- Consumes: `StageScope` (Task 2).
- Produces: `ScopeError(Exception)`, `ScopedFilesystemTool(scope)` with `.read_file(path) -> str`, `.write_file(path, content) -> None`, `.edit_file(path, old, new) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# _server/tests/test_fs_tool.py
from pathlib import Path

import pytest

from app.contract import parse_contract
from app.fs_tool import ScopedFilesystemTool, ScopeError
from app.scope import StageScope

CONTRACT = """---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 01_intended-use.md
    relative_to: run
    access: read
outputs:
  - path: 02_capability.md
    relative_to: run
  - path: build/items/
    relative_to: run
---
prose
"""


@pytest.fixture
def tool(tmp_path: Path) -> ScopedFilesystemTool:
    run_root = tmp_path / "worksheets" / "design-test"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text("| 01 | [ ] |\n")
    (run_root / "01_intended-use.md").write_text("intended use")
    scope = StageScope(
        contract=parse_contract(CONTRACT),
        repo_root=tmp_path,
        stage_dir=tmp_path / "01-design" / "02_capability",
        run_root=run_root,
    )
    scope._rebuild()
    return ScopedFilesystemTool(scope)


def test_reads_a_declared_input(tool: ScopedFilesystemTool):
    assert tool.read_file("01_intended-use.md") == "intended use"


def test_reads_outside_scope_raises(tool: ScopedFilesystemTool):
    with pytest.raises(ScopeError):
        tool.read_file("../../secrets.md")


def test_writes_a_declared_output(tool: ScopedFilesystemTool, tmp_path: Path):
    tool.write_file("02_capability.md", "capability card")
    written = tmp_path / "worksheets" / "design-test" / "02_capability.md"
    assert written.read_text() == "capability card"


def test_writes_to_a_read_only_input_raises(tool: ScopedFilesystemTool):
    with pytest.raises(ScopeError):
        tool.write_file("01_intended-use.md", "overwritten")


def test_writes_into_a_declared_directory(tool: ScopedFilesystemTool, tmp_path: Path):
    tool.write_file("build/items/item-001.json", "{}")
    written = tmp_path / "worksheets" / "design-test" / "build" / "items" / "item-001.json"
    assert written.read_text() == "{}"


def test_edit_file_replaces_first_occurrence(tool: ScopedFilesystemTool, tmp_path: Path):
    tool.write_file("02_capability.md", "draft: todo\nmore text")
    tool.edit_file("02_capability.md", "draft: todo", "draft: done")
    written = tmp_path / "worksheets" / "design-test" / "02_capability.md"
    assert written.read_text() == "draft: done\nmore text"


def test_edit_file_missing_old_text_raises(tool: ScopedFilesystemTool):
    tool.write_file("02_capability.md", "hello")
    with pytest.raises(ScopeError):
        tool.edit_file("02_capability.md", "not present", "new")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd _server && python -m pytest tests/test_fs_tool.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.fs_tool'`

- [ ] **Step 3: Implement**

```python
# _server/app/fs_tool.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_fs_tool.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _server/app/fs_tool.py _server/tests/test_fs_tool.py
git commit -m "Add scoped filesystem tool for stage conversations"
```

---

## Task 5: Run-lifecycle helpers — `RUN.md` ticking, the log index, `create_run`

**Files:**
- Create: `_server/app/run_md.py`
- Create: `_server/app/log_index.py`
- Create: `_server/app/create_run.py`
- Create: `_server/tests/conftest.py`
- Test: `_server/tests/test_run_md.py`
- Test: `_server/tests/test_log_index.py`
- Test: `_server/tests/test_create_run.py`

**Interfaces:**
- Produces (`run_md.py`): `RunMdError(Exception)`, `tick_stage(text, stage) -> str`, `untick_stage(text, stage) -> str`, `add_loop_back(text, date, from_stage, back_to_stage, forced_by, what_changed) -> str`.
- Produces (`log_index.py`): `append_run(repo_root, slug, mode, subject, opened) -> None`, `commit_log_index(repo_root, slug) -> None`.
- Produces (`create_run.py`): `CreateRunError(Exception)`, `create_run(repo_root, pipeline, slug, subject) -> Path` (returns the new run folder).
- Produces (`conftest.py`): pytest fixture `tmp_repo(tmp_path) -> Path`, a throwaway copy of `_shared/`, `_templates/design-run/`, `01-design/` (with Task 3's frontmatter already in it), and `worksheets/_index/`, initialized as its own git repo. Every later task that needs a real, mutate-able repo copy uses this fixture.

- [ ] **Step 1: Write the failing tests**

```python
# _server/tests/conftest.py
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REAL_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    for rel in ("_shared", "_templates/design-run", "01-design"):
        shutil.copytree(REAL_REPO_ROOT / rel, repo / rel)
    (repo / "worksheets" / "_index").mkdir(parents=True)
    shutil.copy(
        REAL_REPO_ROOT / "worksheets" / "_index" / "log.md",
        repo / "worksheets" / "_index" / "log.md",
    )
    shutil.copy(
        REAL_REPO_ROOT / "worksheets" / "CONTEXT.md",
        repo / "worksheets" / "CONTEXT.md",
    )

    def run(*args: str) -> None:
        subprocess.run(args, cwd=repo, check=True, capture_output=True)

    run("git", "init")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test")
    run("git", "add", "-A")
    run("git", "commit", "-m", "initial")
    return repo
```

```python
# _server/tests/test_run_md.py
import pytest

from app.run_md import RunMdError, add_loop_back, tick_stage, untick_stage

SAMPLE = """# A run

| File | Stage | Questions | Done |
|---|---|---|---|
| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |
| `02_capability.md` | 02 | Q3–Q5 | [ ] |

## Loop-backs

| Date | From stage | Back to stage | What forced it | What changed |
|---|---|---|---|---|
"""


def test_tick_stage_sets_only_the_matching_row():
    result = tick_stage(SAMPLE, "01")
    assert "| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [x] |" in result
    assert "| `02_capability.md` | 02 | Q3–Q5 | [ ] |" in result


def test_tick_unknown_stage_raises():
    with pytest.raises(RunMdError):
        tick_stage(SAMPLE, "99")


def test_untick_stage_reverses_a_tick():
    ticked = tick_stage(SAMPLE, "01")
    result = untick_stage(ticked, "01")
    assert "| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |" in result


def test_add_loop_back_appends_a_row():
    result = add_loop_back(
        SAMPLE,
        date="2026-09-09",
        from_stage="07",
        back_to_stage="02",
        forced_by="capability too vague",
        what_changed="tightened the definition",
    )
    assert "| 2026-09-09 | 07 | 02 | capability too vague | tightened the definition |" in result
```

```python
# _server/tests/test_log_index.py
import subprocess
from pathlib import Path

from app.log_index import append_run, commit_log_index


def test_append_run_adds_a_row(tmp_repo: Path):
    log_path = tmp_repo / "worksheets" / "_index" / "log.md"
    before = log_path.read_text(encoding="utf-8")
    append_run(tmp_repo, "design-my-eval", "design", "A test eval", "2026-09-09")
    after = log_path.read_text(encoding="utf-8")
    assert after.startswith(before)
    assert "| design-my-eval | design | A test eval | 2026-09-09 | |" in after


def test_commit_log_index_commits_only_that_file(tmp_repo: Path):
    append_run(tmp_repo, "design-my-eval", "design", "A test eval", "2026-09-09")
    commit_log_index(tmp_repo, "design-my-eval")
    log_show = subprocess.run(
        ["git", "show", "--stat", "HEAD"], cwd=tmp_repo, check=True, capture_output=True, text=True,
    ).stdout
    assert "worksheets/_index/log.md" in log_show
    assert "design-my-eval" in subprocess.run(
        ["git", "log", "-1", "--format=%s"], cwd=tmp_repo, check=True, capture_output=True, text=True,
    ).stdout
```

```python
# _server/tests/test_create_run.py
import pytest

from app.create_run import CreateRunError, create_run


def test_creates_run_folder_from_template(tmp_repo):
    run_root = create_run(tmp_repo, "design", "my-eval", "A test eval")
    assert run_root == tmp_repo / "worksheets" / "design-my-eval"
    assert (run_root / "RUN.md").exists()
    assert (run_root / "01_intended-use.md").exists()


def test_stamps_slug_and_opened_date_into_run_md(tmp_repo):
    run_root = create_run(tmp_repo, "design", "my-eval", "A test eval")
    run_md = (run_root / "RUN.md").read_text(encoding="utf-8")
    assert "slug: design-my-eval" in run_md
    assert "slug: design-<kebab-slug>" not in run_md
    assert "opened: YYYY-MM-DD" not in run_md


def test_records_the_run_in_the_log_index(tmp_repo):
    create_run(tmp_repo, "design", "my-eval", "A test eval")
    log_text = (tmp_repo / "worksheets" / "_index" / "log.md").read_text(encoding="utf-8")
    assert "| design-my-eval | design | A test eval |" in log_text


def test_colliding_slug_raises(tmp_repo):
    create_run(tmp_repo, "design", "my-eval", "A test eval")
    with pytest.raises(CreateRunError):
        create_run(tmp_repo, "design", "my-eval", "A different eval")


def test_unsupported_pipeline_raises(tmp_repo):
    with pytest.raises(CreateRunError):
        create_run(tmp_repo, "audit", "my-eval", "A test eval")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd _server && python -m pytest tests/test_run_md.py tests/test_log_index.py tests/test_create_run.py -v`
Expected: FAIL — `ModuleNotFoundError` for each new module

- [ ] **Step 3: Implement**

```python
# _server/app/run_md.py
from __future__ import annotations

import re


class RunMdError(Exception):
    pass


def _find_stage_line_index(lines: list[str], stage: str) -> int:
    pattern = re.compile(rf"^\|\s*`[^`]+`\s*\|\s*{re.escape(stage)}\s*\|")
    for i, line in enumerate(lines):
        if pattern.match(line):
            return i
    raise RunMdError(f"stage '{stage}' not found in RUN.md stage table")


def tick_stage(text: str, stage: str) -> str:
    lines = text.splitlines(keepends=True)
    idx = _find_stage_line_index(lines, stage)
    lines[idx] = lines[idx].replace("[ ]", "[x]")
    return "".join(lines)


def untick_stage(text: str, stage: str) -> str:
    lines = text.splitlines(keepends=True)
    idx = _find_stage_line_index(lines, stage)
    lines[idx] = lines[idx].replace("[x]", "[ ]")
    return "".join(lines)


_LOOPBACK_HEADER = (
    "| Date | From stage | Back to stage | What forced it | What changed |\n"
    "|---|---|---|---|---|\n"
)


def add_loop_back(
    text: str, date: str, from_stage: str, back_to_stage: str, forced_by: str, what_changed: str
) -> str:
    if _LOOPBACK_HEADER not in text:
        raise RunMdError("loop-back table header not found in RUN.md")
    row = f"| {date} | {from_stage} | {back_to_stage} | {forced_by} | {what_changed} |\n"
    return text.replace(_LOOPBACK_HEADER, _LOOPBACK_HEADER + row, 1)
```

```python
# _server/app/log_index.py
"""Append a run to worksheets/_index/log.md and commit it -- the one place
this backend ever touches git, since that file (unlike a run folder) is
tracked. See docs/decisions/2026-09-09-orchestration-backend.md."""
from __future__ import annotations

import subprocess
from pathlib import Path


def append_run(repo_root: Path, slug: str, mode: str, subject: str, opened: str) -> None:
    log_path = repo_root / "worksheets" / "_index" / "log.md"
    text = log_path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    row = f"| {slug} | {mode} | {subject} | {opened} | |\n"
    log_path.write_text(text + row, encoding="utf-8")


def commit_log_index(repo_root: Path, slug: str) -> None:
    rel_path = "worksheets/_index/log.md"
    subprocess.run(["git", "add", rel_path], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"Add {slug} to the run log"],
        cwd=repo_root, check=True, capture_output=True,
    )
```

```python
# _server/app/create_run.py
"""The one privileged tool that may create a new run folder. Offered to a
stage's model conversation only when its contract declares bootstrap: true.
Only 'design' is supported until 02-audit and 03-measure get the same
frontmatter treatment as 01-design (Task 3)."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil

from . import log_index

_PIPELINE_TEMPLATES = {"design": "design-run"}


class CreateRunError(Exception):
    pass


def create_run(repo_root: Path, pipeline: str, slug: str, subject: str) -> Path:
    if pipeline not in _PIPELINE_TEMPLATES:
        raise CreateRunError(f"pipeline '{pipeline}' is not supported yet")

    full_slug = slug if slug.startswith(f"{pipeline}-") else f"{pipeline}-{slug}"
    run_root = repo_root / "worksheets" / full_slug
    if run_root.exists():
        raise CreateRunError(f"a run named '{full_slug}' already exists")

    template_root = repo_root / "_templates" / _PIPELINE_TEMPLATES[pipeline]
    if not template_root.exists():
        raise CreateRunError(f"template folder missing: {template_root}")
    shutil.copytree(template_root, run_root)

    opened = date.today().isoformat()
    run_md_path = run_root / "RUN.md"
    text = run_md_path.read_text(encoding="utf-8")
    text = text.replace(f"slug: {pipeline}-<kebab-slug>", f"slug: {full_slug}", 1)
    text = text.replace("opened: YYYY-MM-DD", f"opened: {opened}", 1)
    run_md_path.write_text(text, encoding="utf-8")

    log_index.append_run(repo_root, full_slug, pipeline, subject, opened)
    log_index.commit_log_index(repo_root, full_slug)
    return run_root
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_run_md.py tests/test_log_index.py tests/test_create_run.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _server/app/run_md.py _server/app/log_index.py _server/app/create_run.py _server/tests/conftest.py _server/tests/test_run_md.py _server/tests/test_log_index.py _server/tests/test_create_run.py
git commit -m "Add RUN.md helpers, log index commit, and create_run"
```

---

## Task 6: Transcript store & session-start snapshot diff

**Files:**
- Create: `_server/app/transcript.py`
- Create: `_server/app/snapshot.py`
- Test: `_server/tests/test_transcript.py`
- Test: `_server/tests/test_snapshot.py`

**Interfaces:**
- Produces (`transcript.py`): `TranscriptStore(path: Path)` with `.append(turn: dict) -> None`, `.read_all() -> list[dict]`.
- Produces (`snapshot.py`): `SnapshotStore(snapshot_dir: Path)` with `.capture(declared_path: str, current_content: str) -> None` (no-op if already captured this session) and `.diff(declared_path: str, current_content: str) -> str` (unified diff text).

- [ ] **Step 1: Write the failing tests**

```python
# _server/tests/test_transcript.py
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
```

```python
# _server/tests/test_snapshot.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd _server && python -m pytest tests/test_transcript.py tests/test_snapshot.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# _server/app/transcript.py
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
```

```python
# _server/app/snapshot.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_transcript.py tests/test_snapshot.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _server/app/transcript.py _server/app/snapshot.py _server/tests/test_transcript.py _server/tests/test_snapshot.py
git commit -m "Add transcript store and session-start snapshot diff"
```

---

## Task 7: Model client anti-corruption layer

**Files:**
- Create: `_server/app/model_client.py`
- Create: `_server/tests/fakes.py`
- Test: `_server/tests/test_model_client.py`

**Interfaces:**
- Produces: `TextBlock(text)`, `ToolUseBlock(id, name, input)`, `ModelResponse(content, stop_reason)`, `ModelClient` (a `typing.Protocol` with `.create(system, messages, tools) -> ModelResponse`), `AnthropicModelClient(api_key=None, model="claude-sonnet-5", client=None)` implementing `ModelClient` by wrapping the real SDK.
- Produces (`tests/fakes.py`, shared test helper, not part of `app/`): `FakeModelClient(responses: list[ModelResponse])` implementing `ModelClient` — returns each scripted response in order, records every call's `messages`/`tools` for assertions, raises `AssertionError` if called more times than it has scripted responses.

- [ ] **Step 1: Write the failing test**

```python
# _server/tests/test_model_client.py
from types import SimpleNamespace

from app.model_client import AnthropicModelClient, TextBlock, ToolUseBlock


class FakeSDKClient:
    """Stands in for anthropic.Anthropic -- only the .messages.create shape
    that AnthropicModelClient depends on."""

    def __init__(self, sdk_response):
        self._response = sdk_response
        self.messages = SimpleNamespace(create=self._create)
        self.last_call = None

    def _create(self, **kwargs):
        self.last_call = kwargs
        return self._response


def test_converts_text_block():
    sdk_response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hello")],
        stop_reason="end_turn",
    )
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk)

    result = client.create(system=[], messages=[], tools=[])

    assert result.content == [TextBlock(text="hello")]
    assert result.stop_reason == "end_turn"


def test_converts_tool_use_block():
    sdk_response = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", id="call_1", name="write_file", input={"path": "a.md"})],
        stop_reason="tool_use",
    )
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk)

    result = client.create(system=[], messages=[], tools=[])

    assert result.content == [ToolUseBlock(id="call_1", name="write_file", input={"path": "a.md"})]


def test_passes_system_messages_and_tools_through(): 
    sdk_response = SimpleNamespace(content=[], stop_reason="end_turn")
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk, model="claude-sonnet-5")

    client.create(system=[{"type": "text", "text": "sys"}], messages=[{"role": "user", "content": []}], tools=[{"name": "read_file"}])

    assert fake_sdk.last_call["model"] == "claude-sonnet-5"
    assert fake_sdk.last_call["system"] == [{"type": "text", "text": "sys"}]
    assert fake_sdk.last_call["tools"] == [{"name": "read_file"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd _server && python -m pytest tests/test_model_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.model_client'`

- [ ] **Step 3: Implement**

```python
# _server/app/model_client.py
"""Anti-corruption layer over the Anthropic SDK: everything downstream
(stage_runner.py, and every test) only ever sees TextBlock / ToolUseBlock /
ModelResponse, never the SDK's own response types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Union


@dataclass(frozen=True)
class TextBlock:
    text: str


@dataclass(frozen=True)
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]


ContentBlock = Union[TextBlock, ToolUseBlock]


@dataclass(frozen=True)
class ModelResponse:
    content: list[ContentBlock]
    stop_reason: str


class ModelClient(Protocol):
    def create(
        self,
        system: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelResponse: ...


class AnthropicModelClient:
    """Wraps the real Anthropic SDK. Pass `client` in tests to substitute a
    fake with the same `.messages.create(...)` shape."""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-5", client: Any = None):
        if client is not None:
            self._client = client
        else:
            import anthropic

            self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def create(self, system, messages, tools) -> ModelResponse:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=tools,
        )
        content: list[ContentBlock] = []
        for block in response.content:
            if block.type == "text":
                content.append(TextBlock(text=block.text))
            elif block.type == "tool_use":
                content.append(ToolUseBlock(id=block.id, name=block.name, input=block.input))
        return ModelResponse(content=content, stop_reason=response.stop_reason)
```

```python
# _server/tests/fakes.py
"""Shared test doubles. Not part of app/ -- imported only by tests."""
from __future__ import annotations

from typing import Any

from app.model_client import ModelResponse


class FakeModelClient:
    def __init__(self, responses: list[ModelResponse]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, system, messages, tools) -> ModelResponse:
        self.calls.append({"system": system, "messages": messages, "tools": tools})
        if not self._responses:
            raise AssertionError("FakeModelClient called more times than it has scripted responses")
        return self._responses.pop(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_model_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _server/app/model_client.py _server/tests/fakes.py _server/tests/test_model_client.py
git commit -m "Add Anthropic model client anti-corruption layer"
```

---

## Task 8: Stage Runner — the conversation loop

**Files:**
- Create: `_server/app/stage_runner.py`
- Test: `_server/tests/test_stage_runner.py`

**Interfaces:**
- Consumes: `StageScope` (Task 2), `ScopedFilesystemTool`/`ScopeError` (Task 4), `tick_stage` (Task 5), `create_run`/`CreateRunError` (Task 5), `TranscriptStore` (Task 6), `ModelClient`/`ModelResponse`/`TextBlock`/`ToolUseBlock` (Task 7), `FakeModelClient` (Task 7, tests only).
- Produces: `IterationLimitExceeded(Exception)`, `StageRunner(scope, model_client, transcript, repo_root, pipeline, stage_number)` with `.send(user_message: str | None) -> str` and `.ready_for_review: bool`.

- [ ] **Step 1: Write the failing tests**

```python
# _server/tests/test_stage_runner.py
from pathlib import Path

import pytest

from app.model_client import ModelResponse, TextBlock, ToolUseBlock
from app.scope import load_stage_scope
from app.stage_runner import IterationLimitExceeded, StageRunner
from app.transcript import TranscriptStore
from tests.fakes import FakeModelClient


def _stage_01_scope(tmp_repo: Path):
    return load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=None,
    )


def test_text_only_turn_returns_immediately_and_records_transcript(tmp_repo: Path, tmp_path: Path):
    client = FakeModelClient([ModelResponse(content=[TextBlock(text="what should this measure?")], stop_reason="end_turn")])
    runner = StageRunner(
        scope=_stage_01_scope(tmp_repo),
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    reply = runner.send("I need an eval for summary faithfulness")

    assert reply == "what should this measure?"
    turns = TranscriptStore(tmp_path / "session.jsonl").read_all()
    assert turns[0]["role"] == "user"
    assert turns[1]["role"] == "assistant"


def test_create_run_tool_call_creates_the_run_and_binds_scope(tmp_repo: Path, tmp_path: Path):
    client = FakeModelClient([
        ModelResponse(
            content=[ToolUseBlock(id="call_1", name="create_run", input={"slug": "my-eval", "subject": "A test eval"})],
            stop_reason="tool_use",
        ),
        ModelResponse(content=[TextBlock(text="run created")], stop_reason="end_turn"),
    ])
    scope = _stage_01_scope(tmp_repo)
    runner = StageRunner(
        scope=scope,
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    runner.send("start a run")

    assert (tmp_repo / "worksheets" / "design-my-eval" / "RUN.md").exists()
    assert scope.run_root == tmp_repo / "worksheets" / "design-my-eval"


def test_write_file_then_mark_ready_for_review(tmp_repo: Path, tmp_path: Path):
    client = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "subj"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="write_file", input={"path": "01_intended-use.md", "content": "the use case"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c3", name="mark_ready_for_review", input={}) ], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="drafted, ready for your review")], stop_reason="end_turn"),
    ])
    scope = _stage_01_scope(tmp_repo)
    runner = StageRunner(
        scope=scope,
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    reply = runner.send("go")

    assert reply == "drafted, ready for your review"
    assert runner.ready_for_review is True
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    assert (run_root / "01_intended-use.md").read_text() == "the use case"
    assert "[x]" in (run_root / "RUN.md").read_text()


def test_tool_error_is_reported_back_to_the_model_not_raised(tmp_repo: Path, tmp_path: Path):
    client = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="write_file", input={"path": "not-declared.md", "content": "x"})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="understood, that path isn't available")], stop_reason="end_turn"),
    ])
    runner = StageRunner(
        scope=_stage_01_scope(tmp_repo),
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    reply = runner.send("go")

    assert reply == "understood, that path isn't available"
    turns = TranscriptStore(tmp_path / "session.jsonl").read_all()
    tool_result_turn = turns[2]
    assert tool_result_turn["content"][0]["is_error"] is True


def test_runaway_tool_loop_raises_iteration_limit(tmp_repo: Path, tmp_path: Path):
    responses = [
        ModelResponse(content=[ToolUseBlock(id=f"c{i}", name="read_file", input={"path": "_shared/ecbd-framework.md"})], stop_reason="tool_use")
        for i in range(40)
    ]
    client = FakeModelClient(responses)
    runner = StageRunner(
        scope=_stage_01_scope(tmp_repo),
        model_client=client,
        transcript=TranscriptStore(tmp_path / "session.jsonl"),
        repo_root=tmp_repo,
        pipeline="design",
        stage_number="01",
    )

    with pytest.raises(IterationLimitExceeded):
        runner.send("go")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd _server && python -m pytest tests/test_stage_runner.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.stage_runner'`

- [ ] **Step 3: Implement**

```python
# _server/app/stage_runner.py
"""The per-stage conversation loop: call the model, dispatch any tool_use
blocks against this stage's scoped tools, and stop at the first text-only
turn. Whether that turn is a clarifying question or "drafted, ready for
review" is for the human reading it to judge -- both are the same
stop-and-wait point in this loop."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contract import ContractError
from .create_run import CreateRunError, create_run
from .fs_tool import ScopedFilesystemTool, ScopeError
from .model_client import ModelClient, ModelResponse, TextBlock, ToolUseBlock
from .run_md import tick_stage
from .scope import StageScope
from .transcript import TranscriptStore

MAX_TOOL_ITERATIONS = 30


class IterationLimitExceeded(Exception):
    pass


_BASE_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the content of a file declared in this stage's Inputs.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file declared in this stage's Outputs or a read-write Input.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace the first occurrence of old text with new text in a writable file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old": {"type": "string"},
                "new": {"type": "string"},
            },
            "required": ["path", "old", "new"],
        },
    },
    {
        "name": "mark_ready_for_review",
        "description": "Tick this stage's row in RUN.md: a draft exists and is ready for the human check.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

_CREATE_RUN_TOOL = {
    "name": "create_run",
    "description": "Create this run's folder from the pipeline's template. Usable once, before the run exists.",
    "input_schema": {
        "type": "object",
        "properties": {"slug": {"type": "string"}, "subject": {"type": "string"}},
        "required": ["slug", "subject"],
    },
}


@dataclass
class _ToolResult:
    tool_use_id: str
    content: str
    is_error: bool = False


class StageRunner:
    def __init__(
        self,
        scope: StageScope,
        model_client: ModelClient,
        transcript: TranscriptStore,
        repo_root: Path,
        pipeline: str,
        stage_number: str,
    ):
        self.scope = scope
        self.model_client = model_client
        self.transcript = transcript
        self.repo_root = repo_root
        self.pipeline = pipeline
        self.stage_number = stage_number
        self.fs_tool = ScopedFilesystemTool(scope)
        self.ready_for_review = False

    def _tools(self) -> list[dict[str, Any]]:
        tools = list(_BASE_TOOLS)
        if self.scope.contract.bootstrap and self.scope.run_root is None:
            tools.append(_CREATE_RUN_TOOL)
        return tools

    def _system_prompt(self) -> list[dict[str, Any]]:
        repo_refs = "\n\n".join(
            f"### {spec.path}\n{self.fs_tool.read_file(spec.path)}"
            for spec in self.scope.contract.inputs
            if spec.relative_to in ("repo", "stage") and spec.path in self.scope.readable_files
        )
        run_refs = "\n\n".join(
            f"### {spec.path}\n{self.fs_tool.read_file(spec.path)}"
            for spec in self.scope.contract.inputs
            if spec.relative_to == "run" and spec.path in self.scope.readable_files
        )
        static_text = f"{self.scope.contract.prose}\n\n## Reference material\n{repo_refs}"
        blocks: list[dict[str, Any]] = [
            {"type": "text", "text": static_text, "cache_control": {"type": "ephemeral"}}
        ]
        if run_refs:
            blocks.append({"type": "text", "text": f"## This run's files so far\n{run_refs}"})
        return blocks

    def _dispatch(self, call: ToolUseBlock) -> _ToolResult:
        try:
            if call.name == "read_file":
                return _ToolResult(call.id, self.fs_tool.read_file(call.input["path"]))
            if call.name == "write_file":
                self.fs_tool.write_file(call.input["path"], call.input["content"])
                return _ToolResult(call.id, f"wrote {call.input['path']}")
            if call.name == "edit_file":
                self.fs_tool.edit_file(call.input["path"], call.input["old"], call.input["new"])
                return _ToolResult(call.id, f"edited {call.input['path']}")
            if call.name == "mark_ready_for_review":
                return self._mark_ready_for_review(call)
            if call.name == "create_run":
                return self._create_run(call)
            return _ToolResult(call.id, f"unknown tool '{call.name}'", is_error=True)
        except (ScopeError, ContractError, CreateRunError) as exc:
            return _ToolResult(call.id, str(exc), is_error=True)

    def _mark_ready_for_review(self, call: ToolUseBlock) -> _ToolResult:
        run_md_path = self.scope.writable_files.get("RUN.md") or self.scope.readable_files.get("RUN.md")
        if run_md_path is None:
            raise ScopeError("RUN.md is not in this stage's scope")
        text = run_md_path.read_text(encoding="utf-8")
        run_md_path.write_text(tick_stage(text, self.stage_number), encoding="utf-8")
        self.ready_for_review = True
        return _ToolResult(call.id, "marked ready for review")

    def _create_run(self, call: ToolUseBlock) -> _ToolResult:
        run_root = create_run(self.repo_root, self.pipeline, call.input["slug"], call.input["subject"])
        self.scope.bind_run_root(run_root)
        return _ToolResult(call.id, f"created run at {run_root}")

    def send(self, user_message: str | None) -> str:
        messages = [
            {"role": t["role"], "content": t["content"]} for t in self.transcript.read_all()
        ]
        if user_message is not None:
            entry = {"role": "user", "content": [{"type": "text", "text": user_message}]}
            self.transcript.append(entry)
            messages.append(entry)

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self.model_client.create(
                system=self._system_prompt(), messages=messages, tools=self._tools()
            )
            assistant_entry = {"role": "assistant", "content": _blocks_to_dicts(response)}
            self.transcript.append(assistant_entry)
            messages.append(assistant_entry)

            tool_calls = [b for b in response.content if isinstance(b, ToolUseBlock)]
            if not tool_calls:
                return "".join(b.text for b in response.content if isinstance(b, TextBlock))

            results = [self._dispatch(call) for call in tool_calls]
            tool_entry = {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": r.tool_use_id,
                        "content": r.content,
                        "is_error": r.is_error,
                    }
                    for r in results
                ],
            }
            self.transcript.append(tool_entry)
            messages.append(tool_entry)

        raise IterationLimitExceeded(
            f"stage {self.stage_number} exceeded {MAX_TOOL_ITERATIONS} tool-call iterations"
        )


def _blocks_to_dicts(response: ModelResponse) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for b in response.content:
        if isinstance(b, TextBlock):
            blocks.append({"type": "text", "text": b.text})
        elif isinstance(b, ToolUseBlock):
            blocks.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
    return blocks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_stage_runner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _server/app/stage_runner.py _server/tests/test_stage_runner.py
git commit -m "Add the per-stage conversation loop"
```

---

## Task 9: Approve / reject a stage

**Files:**
- Create: `_server/app/approval.py`
- Test: `_server/tests/test_approval.py`

**Interfaces:**
- Consumes: `StageScope` (Task 2), `tick_stage`/`untick_stage`/`add_loop_back` (Task 5).
- Produces: `ApprovalError(Exception)`, `ApprovalResult(approved_stage, approved_outputs)`, `approve_stage(scope, stage_number) -> ApprovalResult`, `reject_stage(scope, from_stage, target_stage, reason) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# _server/tests/test_approval.py
from pathlib import Path

import pytest

from app.approval import ApprovalError, approve_stage, reject_stage
from app.scope import load_stage_scope


def _prepare_stage_01_run(tmp_repo: Path) -> Path:
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)
    (run_root / "RUN.md").write_text(
        "| File | Stage | Questions | Done |\n"
        "|---|---|---|---|\n"
        "| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |\n"
        "\n## Loop-backs\n\n"
        "| Date | From stage | Back to stage | What forced it | What changed |\n"
        "|---|---|---|---|---|\n"
    )
    return run_root


def test_approve_fails_when_output_missing(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )
    with pytest.raises(ApprovalError):
        approve_stage(scope, "01")


def test_approve_ticks_run_md_when_output_exists(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    (run_root / "01_intended-use.md").write_text("the intended use, in full")
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )

    result = approve_stage(scope, "01")

    assert result.approved_stage == "01"
    assert "[x]" in (run_root / "RUN.md").read_text()


def test_approve_fails_on_empty_output(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    (run_root / "01_intended-use.md").write_text("")
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )
    with pytest.raises(ApprovalError):
        approve_stage(scope, "01")


def test_reject_unticks_and_adds_loop_back_row(tmp_repo: Path):
    run_root = _prepare_stage_01_run(tmp_repo)
    (run_root / "01_intended-use.md").write_text("the intended use")
    scope = load_stage_scope(
        tmp_repo / "01-design" / "01_intended-use" / "CONTEXT.md",
        repo_root=tmp_repo,
        run_root=run_root,
    )
    approve_stage(scope, "01")

    reject_stage(scope, from_stage="01", target_stage="01", reason="vague decision")

    text = (run_root / "RUN.md").read_text()
    assert "[ ]" in text
    assert "vague decision" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd _server && python -m pytest tests/test_approval.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.approval'`

- [ ] **Step 3: Implement**

```python
# _server/app/approval.py
"""Stage approval and rejection -- the human-check gate. Enforces that a
stage's declared outputs actually exist before the next stage becomes
reachable, and records loop-backs when a human sends work back to an
earlier stage. No git operation happens here; see
docs/decisions/2026-09-09-orchestration-backend.md."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .run_md import add_loop_back, tick_stage, untick_stage
from .scope import StageScope


class ApprovalError(Exception):
    pass


@dataclass
class ApprovalResult:
    approved_stage: str
    approved_outputs: list[str]


def _run_md_path(scope: StageScope):
    path = scope.writable_files.get("RUN.md") or scope.readable_files.get("RUN.md")
    if path is None:
        raise ApprovalError("RUN.md is not in this stage's scope")
    return path


def approve_stage(scope: StageScope, stage_number: str) -> ApprovalResult:
    missing = []
    for spec in scope.contract.outputs:
        if spec.is_directory:
            continue  # directory outputs may legitimately be empty
        target = scope.writable_files.get(spec.path)
        if target is None or not target.exists() or target.stat().st_size == 0:
            missing.append(spec.path)
    if missing:
        raise ApprovalError(f"cannot approve: outputs not written yet: {missing}")

    run_md_path = _run_md_path(scope)
    text = run_md_path.read_text(encoding="utf-8")
    run_md_path.write_text(tick_stage(text, stage_number), encoding="utf-8")

    return ApprovalResult(
        approved_stage=stage_number,
        approved_outputs=[spec.path for spec in scope.contract.outputs if not spec.is_directory],
    )


def reject_stage(scope: StageScope, from_stage: str, target_stage: str, reason: str) -> None:
    run_md_path = _run_md_path(scope)
    text = run_md_path.read_text(encoding="utf-8")
    text = untick_stage(text, from_stage)
    text = add_loop_back(
        text,
        date=date.today().isoformat(),
        from_stage=from_stage,
        back_to_stage=target_stage,
        forced_by=reason,
        what_changed="pending",
    )
    run_md_path.write_text(text, encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_approval.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _server/app/approval.py _server/tests/test_approval.py
git commit -m "Add stage approval and rejection (the human-check gate)"
```

---

## Task 10: Stage Session API

**Files:**
- Modify: `_server/app/main.py`
- Test: `_server/tests/test_api.py`

**Interfaces:**
- Consumes: everything from Tasks 2, 4–9.
- Produces: `create_app(model_client: ModelClient | None = None, repo_root: Path | None = None) -> FastAPI` — the two new parameters make the app injectable for tests without touching global state or environment variables.

Routes added: `GET /runs`, `POST /runs/{pipeline}/start`, `POST /sessions/{id}/messages`, `GET /sessions/{id}`, `POST /runs/{slug}/stages/{stage}/approve`, `POST /runs/{slug}/stages/{stage}/reject`, `GET /runs/{slug}/diff/{stage}`.

- [ ] **Step 1: Write the failing test**

```python
# _server/tests/test_api.py
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.model_client import ModelResponse, TextBlock, ToolUseBlock
from tests.fakes import FakeModelClient


def test_full_stage_1_to_stage_2_flow_with_a_loop_back(tmp_repo: Path):
    client_stage_1 = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "A faithfulness eval"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="write_file", input={"path": "01_intended-use.md", "content": "the intended use, spelled out"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c3", name="mark_ready_for_review", input={})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="drafted, ready for review")], stop_reason="end_turn"),
    ])
    app = create_app(model_client=client_stage_1, repo_root=tmp_repo)
    api = TestClient(app)

    start = api.post("/runs/design/start", json={"brief": "I need a faithfulness eval"})
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    session = api.get(f"/sessions/{session_id}")
    assert session.status_code == 200
    assert len(session.json()["transcript"]) >= 2

    diff = api.get("/runs/design-my-eval/diff/01")
    assert diff.status_code == 200
    assert "+the intended use, spelled out" in diff.json()["diff"]

    approve = api.post("/runs/design-my-eval/stages/01/approve")
    assert approve.status_code == 200

    runs = api.get("/runs").json()
    assert any(r["slug"] == "design-my-eval" for r in runs)

    # Stage 2 becomes reachable now that stage 1 is approved.
    client_stage_2 = FakeModelClient([
        ModelResponse(content=[TextBlock(text="what capability does this eval target?")], stop_reason="end_turn"),
    ])
    app.dependency_overrides.clear()
    app2 = create_app(model_client=client_stage_2, repo_root=tmp_repo)
    api2 = TestClient(app2)
    stage_2_start = api2.post("/runs/design-my-eval/stages/02/start", json={"brief": "let's define the capability"})
    assert stage_2_start.status_code == 200

    # A rejection sends stage 2 back to stage 1 and records why.
    reject = api2.post(
        "/runs/design-my-eval/stages/02/reject",
        json={"target_stage": "01", "reason": "intended use was too vague"},
    )
    assert reject.status_code == 200
    run_md = (tmp_repo / "worksheets" / "design-my-eval" / "RUN.md").read_text()
    assert "intended use was too vague" in run_md


def test_start_stage_2_before_stage_1_is_approved_is_rejected(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.post("/runs/design-my-eval/stages/02/start", json={"brief": "go"})
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd _server && python -m pytest tests/test_api.py -v`
Expected: FAIL — `TypeError: create_app() got an unexpected keyword argument 'model_client'`

- [ ] **Step 3: Implement**

```python
# _server/app/main.py
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .approval import ApprovalError, approve_stage, reject_stage
from .contract import ContractError
from .model_client import AnthropicModelClient, ModelClient
from .scope import load_stage_scope
from .snapshot import SnapshotStore
from .stage_runner import StageRunner
from .transcript import TranscriptStore

_STAGE_ORDER = ["01", "02", "03", "04", "05", "06", "07", "08"]
_STAGE_DIRS = {
    "01": "01_intended-use", "02": "02_capability", "03": "03_content",
    "04": "04_adaptation", "05": "05_assembly", "06": "06_evidence",
    "07": "07_validity-review", "08": "08_build",
}


class StartSessionRequest(BaseModel):
    brief: str


class RejectRequest(BaseModel):
    target_stage: str
    reason: str


def create_app(model_client: ModelClient | None = None, repo_root: Path | None = None) -> FastAPI:
    repo_root = repo_root or Path(".").resolve()
    app = FastAPI(title="ecbd-workspace orchestration backend")
    sessions: dict[str, StageRunner] = {}

    def get_model_client() -> ModelClient:
        return model_client or AnthropicModelClient()

    def stage_contract_path(stage: str) -> Path:
        return repo_root / "01-design" / _STAGE_DIRS[stage] / "CONTEXT.md"

    def run_stage_table(slug: str) -> str:
        run_md = repo_root / "worksheets" / slug / "RUN.md"
        if not run_md.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        return run_md.read_text(encoding="utf-8")

    def stage_is_approved(slug: str, stage: str) -> bool:
        from .run_md import _find_stage_line_index

        lines = run_stage_table(slug).splitlines()
        idx = _find_stage_line_index(lines, stage)
        return "[x]" in lines[idx]

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/runs")
    def list_runs() -> list[dict[str, Any]]:
        log_path = repo_root / "worksheets" / "_index" / "log.md"
        rows = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|") or line.startswith("| Slug") or line.startswith("|---"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            rows.append({"slug": cols[0], "mode": cols[1], "subject": cols[2], "opened": cols[3]})
        return rows

    def _start_session(pipeline: str, stage: str, run_root: Path | None, brief: str) -> str:
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
        except ContractError as exc:
            raise HTTPException(500, str(exc)) from exc

        session_id = str(uuid.uuid4())
        runner = StageRunner(
            scope=scope,
            model_client=get_model_client(),
            transcript=TranscriptStore(repo_root / ".sessions" / f"{session_id}.jsonl"),
            repo_root=repo_root,
            pipeline=pipeline,
            stage_number=stage,
        )
        sessions[session_id] = runner
        runner.send(brief)
        return session_id

    @app.post("/runs/{pipeline}/start")
    def start_run(pipeline: str, req: StartSessionRequest) -> dict[str, str]:
        if pipeline != "design":
            raise HTTPException(400, f"pipeline '{pipeline}' is not supported yet")
        session_id = _start_session(pipeline, "01", run_root=None, brief=req.brief)
        return {"session_id": session_id}

    @app.post("/runs/{slug}/stages/{stage}/start")
    def start_stage(slug: str, stage: str, req: StartSessionRequest) -> dict[str, str]:
        run_root = repo_root / "worksheets" / slug
        if not run_root.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        stage_index = _STAGE_ORDER.index(stage)
        if stage_index > 0:
            previous_stage = _STAGE_ORDER[stage_index - 1]
            if not stage_is_approved(slug, previous_stage):
                raise HTTPException(404, f"stage {previous_stage} is not approved yet")
        session_id = _start_session(slug.split("-", 1)[0], stage, run_root=run_root, brief=req.brief)
        return {"session_id": session_id}

    @app.post("/sessions/{session_id}/messages")
    def send_message(session_id: str, req: StartSessionRequest) -> dict[str, str]:
        runner = sessions.get(session_id)
        if runner is None:
            raise HTTPException(404, f"no such session '{session_id}'")
        reply = runner.send(req.brief)
        return {"reply": reply}

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        runner = sessions.get(session_id)
        if runner is None:
            raise HTTPException(404, f"no such session '{session_id}'")
        return {"transcript": runner.transcript.read_all(), "ready_for_review": runner.ready_for_review}

    @app.post("/runs/{slug}/stages/{stage}/approve")
    def approve(slug: str, stage: str) -> dict[str, Any]:
        run_root = repo_root / "worksheets" / slug
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
            result = approve_stage(scope, stage)
        except (ContractError, ApprovalError) as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"approved_stage": result.approved_stage, "approved_outputs": result.approved_outputs}

    @app.post("/runs/{slug}/stages/{stage}/reject")
    def reject(slug: str, stage: str, req: RejectRequest) -> dict[str, str]:
        run_root = repo_root / "worksheets" / slug
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
            reject_stage(scope, from_stage=stage, target_stage=req.target_stage, reason=req.reason)
        except ContractError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"status": "rejected"}

    @app.get("/runs/{slug}/diff/{stage}")
    def diff(slug: str, stage: str) -> dict[str, str]:
        # NOTE: this captures the baseline lazily, on first call, rather than
        # precisely at session start as the spec describes. For a stage
        # output that didn't exist before the session (the common case --
        # every design stage writes a file its own template doesn't
        # pre-populate), an empty baseline is correct either way. It is
        # NOT correct for re-diffing a file that already had content before
        # THIS session touched it, if diff() is never called until after
        # several edits. Wiring capture() to fire the moment a session opens
        # (rather than the moment a diff is first requested) is a fast
        # follow, not done in this task -- see "What is not decided".
        run_root = repo_root / "worksheets" / slug
        try:
            scope = load_stage_scope(stage_contract_path(stage), repo_root=repo_root, run_root=run_root)
        except ContractError as exc:
            raise HTTPException(400, str(exc)) from exc
        snapshots = SnapshotStore(repo_root / ".sessions" / f"{slug}-{stage}-snapshots")
        combined = []
        for spec in scope.contract.outputs:
            if spec.is_directory:
                continue
            target = scope.writable_files[spec.path]
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            snapshots.capture(spec.path, "")
            combined.append(snapshots.diff(spec.path, current))
        return {"diff": "\n".join(combined)}

    return app
```

This requires exposing `_find_stage_line_index` from `run_md.py` (Task 5) — it's already a module-level function there, just not previously imported elsewhere; no change to `run_md.py` needed.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_api.py -v`
Expected: PASS

Then run the full suite to confirm nothing else broke:

Run: `cd _server && python -m pytest -v`
Expected: PASS (all tasks' tests)

- [ ] **Step 5: Commit**

```bash
git add _server/app/main.py _server/tests/test_api.py
git commit -m "Wire up the Stage Session API end to end"
```

---

## Self-Review Notes

- **Spec coverage:** Contract Loader/StageScope (spec §"Contract format"), Scoped Filesystem Tool (§"Conversation loop & tools"), `create_run`/log index (§"Bootstrap"/"Decision"), transcript + snapshot (§"Persistence & resuming", §"Human-check gate"), Stage Runner (§"Conversation loop & tools"), approval/rejection (§"Human-check gate & advancement"), API (§"API surface"). Not covered by this plan, deliberately: SSE streaming, `02-audit`/`03-measure` frontmatter, auth (none needed — localhost only). Partially covered: the diff endpoint's snapshot timing is an approximation (see the note inline in Task 10) — correct for every stage in this plan's scope today, since none of their outputs pre-exist a session, but not the general case the spec describes.
- **Placeholder scan:** no TBDs; every step has runnable code and a concrete command.
- **Type/name consistency checked:** `StageScope.resolve_readable`/`resolve_writable` (Task 2) used identically in `fs_tool.py` (Task 4), `stage_runner.py` (Task 8), and `approval.py` (Task 9) via `writable_files`/`readable_files` dict access — verified the attribute names match across all four files. `ModelClient`/`ModelResponse`/`TextBlock`/`ToolUseBlock` (Task 7) are the exact names imported in `stage_runner.py` (Task 8) and `tests/fakes.py`. `create_run(repo_root, pipeline, slug, subject)`'s signature (Task 5) matches its call site in `stage_runner._create_run` (Task 8).

---

**Plan complete and saved to `docs/superpowers/plans/2026-09-09-orchestration-backend-plan.md`.** Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
