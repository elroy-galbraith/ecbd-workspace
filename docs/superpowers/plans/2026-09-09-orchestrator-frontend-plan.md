# Orchestrator Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React/Vite/TypeScript frontend that drives the orchestration backend through the full `01-design` pipeline stage loop — run list, start a run, per-stage chat, document viewer/editor, diff, approve/reject.

**Architecture:** A single-page app talking to the existing FastAPI backend (`_server/`) over `fetch`, using React Query for all server state and React Router for navigation. Two backend endpoints the API surface was supposed to have but never got implemented (`GET /runs/:slug`, `GET`/`PUT /runs/:slug/files/:path`) are added first, as a narrow prerequisite — not new design, just finishing what `docs/decisions/2026-09-09-orchestration-backend.md`'s own API table already specifies.

**Tech Stack:** React 18, TypeScript, Vite, `@tanstack/react-query`, `react-router-dom`, Vitest + React Testing Library. Backend: FastAPI (existing), Python stdlib `re`/`yaml` for the new parsing.

**Spec:** `docs/superpowers/specs/2026-09-09-orchestrator-frontend-design.md`

## Global Constraints

- Frontend lives in a new top-level `_client/` directory (factory code, not a pipeline product — matches `_server/`'s own framing in `_server/CONTEXT.md`).
- No streaming, no session resumption after a backend restart, no `list_files` for directory outputs — these are backend gaps the spec explicitly builds around, not fixed by this plan.
- Only the two backend endpoints named above are added. No other backend behavior changes.
- `PUT /runs/:slug/files/:path` must never allow `RUN.md`'s `approved_stages` to change — that fact is exclusively `approve_stage`/`reject_stage`'s to write (see `_server/app/fs_tool.py`'s existing `_would_change_approval` and the regression test history in `git log` for why this is load-bearing).
- All new frontend code goes under `_client/src/`; component tests use Vitest + React Testing Library; hook-consuming components mock `../api/queries` / `../api/mutations` rather than mocking network calls, so component tests stay about rendering logic, not fetch plumbing.
- Backend base URL is `VITE_API_BASE`, defaulting to `http://127.0.0.1:8000`.

---

## Part 1 — Backend prerequisite

### Task 1: `run_md.py` — parse RUN.md into structured data, and share the approval-guard logic

**Files:**
- Modify: `_server/app/run_md.py`
- Modify: `_server/app/fs_tool.py:60-78` (replace `_would_change_approval`'s body with a call to the new shared helper — no behavior change)
- Test: `_server/tests/test_run_md.py`

**Interfaces:**
- Produces (used by Task 2 and Task 3):
  - `parse_frontmatter(text: str) -> dict` — raises `RunMdError` if no frontmatter block
  - `parse_stage_table(text: str) -> list[dict]` — each dict: `{"file": str, "stage": str, "questions": str, "done": bool}`
  - `parse_loop_backs(text: str) -> list[dict]` — each dict: `{"date": str, "from_stage": str, "back_to_stage": str, "forced_by": str, "what_changed": str}`
  - `parse_run_md(text: str) -> dict` — `{"status": ..., "opened": ..., "closed": ..., "approved_stages": [...], "stages": [...], "loop_backs": [...]}`
  - `approved_stages_would_change(current_content: str, new_content: str) -> bool`

- [ ] **Step 1: Write the failing tests**

Append to `_server/tests/test_run_md.py` (reuses the existing module-level `SAMPLE` and `FRONTMATTER_SAMPLE` fixtures already in that file):

```python
from app.run_md import (
    approved_stages_would_change,
    parse_frontmatter,
    parse_loop_backs,
    parse_run_md,
    parse_stage_table,
)


def test_parse_stage_table_parses_rows():
    rows = parse_stage_table(SAMPLE)
    assert rows == [
        {"file": "01_intended-use.md", "stage": "01", "questions": "Framing, Q1–Q2", "done": False},
        {"file": "02_capability.md", "stage": "02", "questions": "Q3–Q5", "done": False},
    ]


def test_parse_stage_table_reflects_a_tick():
    ticked = tick_stage(SAMPLE, "01")
    rows = parse_stage_table(ticked)
    assert rows[0]["done"] is True
    assert rows[1]["done"] is False


def test_parse_loop_backs_empty_table():
    assert parse_loop_backs(SAMPLE) == []


def test_parse_loop_backs_parses_appended_rows():
    result = add_loop_back(
        SAMPLE,
        date="2026-09-09",
        from_stage="07",
        back_to_stage="02",
        forced_by="capability too vague",
        what_changed="tightened the definition",
    )
    assert parse_loop_backs(result) == [
        {
            "date": "2026-09-09",
            "from_stage": "07",
            "back_to_stage": "02",
            "forced_by": "capability too vague",
            "what_changed": "tightened the definition",
        }
    ]


def test_parse_frontmatter_reads_scalars():
    fm = parse_frontmatter(FRONTMATTER_SAMPLE)
    assert fm["status"] == "intake"
    assert fm["slug"] == "design-my-eval"


def test_parse_frontmatter_missing_block_raises():
    with pytest.raises(RunMdError):
        parse_frontmatter(SAMPLE)


def test_parse_run_md_combines_frontmatter_table_and_loopbacks():
    result = parse_run_md(FRONTMATTER_SAMPLE)
    assert result["status"] == "intake"
    assert result["approved_stages"] == []
    assert result["stages"][0] == {
        "file": "01_intended-use.md", "stage": "01", "questions": "Framing, Q1–Q2", "done": False,
    }
    assert result["loop_backs"] == []


def test_approved_stages_would_change_true_when_list_changes():
    changed = add_approved_stage(FRONTMATTER_SAMPLE, "01")
    assert approved_stages_would_change(FRONTMATTER_SAMPLE, changed) is True


def test_approved_stages_would_change_false_for_an_unrelated_edit():
    other_edit = FRONTMATTER_SAMPLE.replace("# A run", "# A run (renamed)")
    assert approved_stages_would_change(FRONTMATTER_SAMPLE, other_edit) is False


def test_approved_stages_would_change_false_when_target_has_no_content_yet():
    assert approved_stages_would_change("", FRONTMATTER_SAMPLE) is True
```

Note the last test: an empty `current_content` (file didn't exist yet) parses to `RunMdError` internally → treated as "no approved stages" (`None`), which differs from `FRONTMATTER_SAMPLE`'s explicit `approved_stages: []` (`[]`) — `None != []` is `True`. This matches the existing (pre-refactor) behavior in `fs_tool.py`, which this task preserves exactly.

- [ ] **Step 2: Run tests to verify they fail**

Run (from `_server/`): `python -m pytest tests/test_run_md.py -v`
Expected: FAIL — `ImportError: cannot import name 'parse_frontmatter'` (and friends).

- [ ] **Step 3: Implement the parsing functions and the shared guard**

Add to `_server/app/run_md.py` (after the existing imports, keep everything already in the file):

```python
import yaml


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        raise RunMdError("RUN.md is missing a frontmatter block")
    end = text.find("\n---", 4)
    if end == -1:
        raise RunMdError("RUN.md frontmatter block is not terminated")
    return yaml.safe_load(text[4:end]) or {}


_STAGE_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]*)\|\s*\[([ xX])\]\s*\|\s*$",
    re.MULTILINE,
)


def parse_stage_table(text: str) -> list[dict]:
    return [
        {
            "file": m.group(1),
            "stage": m.group(2),
            "questions": m.group(3).strip(),
            "done": m.group(4).lower() == "x",
        }
        for m in _STAGE_ROW_RE.finditer(text)
    ]


_LOOPBACK_ROW_RE = re.compile(
    r"^\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*$",
    re.MULTILINE,
)


def parse_loop_backs(text: str) -> list[dict]:
    idx = text.find(_LOOPBACK_HEADER)
    if idx == -1:
        return []
    after = text[idx + len(_LOOPBACK_HEADER):]
    return [
        {
            "date": cols[0], "from_stage": cols[1], "back_to_stage": cols[2],
            "forced_by": cols[3], "what_changed": cols[4],
        }
        for m in _LOOPBACK_ROW_RE.finditer(after)
        for cols in [[g.strip() for g in m.groups()]]
    ]


def parse_run_md(text: str) -> dict:
    frontmatter = parse_frontmatter(text)
    return {
        "status": frontmatter.get("status"),
        "opened": frontmatter.get("opened"),
        "closed": frontmatter.get("closed"),
        "approved_stages": get_approved_stages(text),
        "stages": parse_stage_table(text),
        "loop_backs": parse_loop_backs(text),
    }


def approved_stages_would_change(current_content: str, new_content: str) -> bool:
    """True if writing new_content would change the parsed approved_stages
    list relative to current_content. Shared by ScopedFilesystemTool (blocks
    model-tool writes to RUN.md) and the file-edit API (blocks direct human
    writes) so both enforce the same invariant: approved_stages changes only
    through approve_stage/reject_stage."""
    try:
        current = get_approved_stages(current_content)
    except RunMdError:
        current = None
    try:
        proposed = get_approved_stages(new_content)
    except RunMdError:
        proposed = None
    return current != proposed
```

Note `_LOOPBACK_HEADER` is already defined further down in this file (existing code) — since Python module execution is top-to-bottom but these are all module-level defs evaluated at import time before any function body runs, `parse_loop_backs` referencing `_LOOPBACK_HEADER` works regardless of definition order, but for readability leave the new functions in the order shown, before the existing `add_loop_back` block that already defines `_LOOPBACK_HEADER` — Python resolves the name at call time, not at function-definition time, so this is safe either way.

Now replace `_would_change_approval` in `_server/app/fs_tool.py:60-78` with:

```python
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
```

This is behavior-preserving — same inputs produce the same result as before, just deduplicated into `run_md.py` so the new file-edit endpoint (Task 3) can reuse it without importing from `fs_tool.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_run_md.py tests/test_fs_tool.py -v`
Expected: PASS — all new tests pass, and the pre-existing `test_fs_tool.py` suite is unaffected (confirms the refactor didn't change behavior).

- [ ] **Step 5: Commit**

```bash
git add _server/app/run_md.py _server/app/fs_tool.py _server/tests/test_run_md.py
git commit -m "Add RUN.md parsing and share the approved_stages guard

Extracts parse_run_md/parse_stage_table/parse_loop_backs (used by the
next task's GET /runs/:slug endpoint) and lifts fs_tool.py's
approval-guard check into run_md.py so the upcoming file-edit endpoint
can reuse the same invariant instead of re-deriving it.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: `GET /runs/{slug}` — parsed RUN.md endpoint

**Files:**
- Modify: `_server/app/main.py`
- Test: `_server/tests/test_api.py`

**Interfaces:**
- Consumes: `parse_run_md(text: str) -> dict` and `RunMdError` from Task 1's `run_md.py`; the existing `run_stage_table(slug)` helper already in `main.py` (reads `RUN.md` text, raises `HTTPException(404, ...)` if the run doesn't exist).
- Produces: `GET /runs/{slug}` → `200 {"slug": str, "status": ..., "opened": ..., "closed": ..., "approved_stages": [...], "stages": [...], "loop_backs": [...]}`, or `404` if the run doesn't exist.

- [ ] **Step 1: Write the failing tests**

Append to `_server/tests/test_api.py`:

```python
def test_get_run_returns_parsed_run_md(tmp_repo: Path):
    client_stage_1 = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "A faithfulness eval"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="write_file", input={"path": "01_intended-use.md", "content": "the intended use"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c3", name="mark_ready_for_review", input={})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="drafted")], stop_reason="end_turn"),
    ])
    app = create_app(model_client=client_stage_1, repo_root=tmp_repo)
    api = TestClient(app)
    api.post("/runs/design/start", json={"brief": "I need a faithfulness eval"})

    run = api.get("/runs/design-my-eval")
    assert run.status_code == 200
    body = run.json()
    assert body["slug"] == "design-my-eval"
    assert body["status"] == "intake"
    assert body["approved_stages"] == []
    stage_01 = next(s for s in body["stages"] if s["stage"] == "01")
    assert stage_01["done"] is True
    assert stage_01["file"] == "01_intended-use.md"
    assert body["loop_backs"] == []


def test_get_run_404_for_unknown_slug(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.get("/runs/design-nonexistent")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run (from `_server/`): `python -m pytest tests/test_api.py::test_get_run_returns_parsed_run_md -v`
Expected: FAIL — `404 Not Found` for a route that doesn't exist yet (FastAPI's default for an unmatched route).

- [ ] **Step 3: Implement the endpoint**

In `_server/app/main.py`, add to the imports at the top:

```python
from .run_md import RunMdError, parse_run_md
```

Add the route (place it near the other `/runs/{slug}` routes, e.g. right after `list_runs`):

```python
    @app.get("/runs/{slug}")
    def get_run(slug: str) -> dict[str, Any]:
        text = run_stage_table(slug)
        try:
            parsed = parse_run_md(text)
        except RunMdError as exc:
            raise HTTPException(500, str(exc)) from exc
        return {"slug": slug, **parsed}
```

`run_stage_table` already exists in `main.py` (reads `worksheets/{slug}/RUN.md`, raises 404 if missing) — this route is a thin wrapper around it plus the new parser.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_api.py -v`
Expected: PASS — the two new tests pass, and the full existing `test_api.py` suite still passes (confirms no regression).

- [ ] **Step 5: Commit**

```bash
git add _server/app/main.py _server/tests/test_api.py
git commit -m "Add GET /runs/:slug, the parsed-RUN.md endpoint the API design already specified

Backs the frontend's stage rail and run switcher. No new design --
docs/decisions/2026-09-09-orchestration-backend.md's API table already
named this route; it was simply never implemented.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: `GET`/`PUT /runs/{slug}/files/{path}` — document viewer/editor, plus CORS

**Files:**
- Modify: `_server/app/main.py`
- Test: `_server/tests/test_api.py`

**Interfaces:**
- Consumes: `approved_stages_would_change` from Task 1's `run_md.py`.
- Produces:
  - `GET /runs/{slug}/files/{file_path}` → `200 {"path": str, "content": str}`, `404` if the run or file doesn't exist.
  - `PUT /runs/{slug}/files/{file_path}` (body `{"content": str}`) → `200 {"path": str, "content": str}`, `404` if the run doesn't exist, `400` if the path escapes the run folder or the edit would change `RUN.md`'s `approved_stages`.
  - Module-level helper `_resolve_run_file(run_root: Path, file_path: str) -> Path` — raises `HTTPException(400, ...)` for a path outside `run_root`. Exposed at module scope (not nested in `create_app`) so it's directly unit-testable without spinning up a client.

- [ ] **Step 1: Write the failing tests**

Append to `_server/tests/test_api.py`:

```python
from fastapi import HTTPException


def test_get_file_returns_content(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)
    (run_root / "01_intended-use.md").write_text("hello", encoding="utf-8")

    response = api.get("/runs/design-my-eval/files/01_intended-use.md")
    assert response.status_code == 200
    assert response.json() == {"path": "01_intended-use.md", "content": "hello"}


def test_get_file_404_for_missing_file(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    (tmp_repo / "worksheets" / "design-my-eval").mkdir(parents=True)

    response = api.get("/runs/design-my-eval/files/nope.md")
    assert response.status_code == 404


def test_get_file_404_for_missing_run(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.get("/runs/design-nonexistent/files/nope.md")
    assert response.status_code == 404


def test_put_file_writes_content(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)

    response = api.put("/runs/design-my-eval/files/01_intended-use.md", json={"content": "edited by hand"})
    assert response.status_code == 200
    assert response.json() == {"path": "01_intended-use.md", "content": "edited by hand"}
    assert (run_root / "01_intended-use.md").read_text(encoding="utf-8") == "edited by hand"


def test_put_file_rejects_changing_approved_stages(tmp_repo: Path):
    client_stage_1 = FakeModelClient([
        ModelResponse(content=[ToolUseBlock(id="c1", name="create_run", input={"slug": "my-eval", "subject": "A faithfulness eval"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c2", name="write_file", input={"path": "01_intended-use.md", "content": "the intended use"})], stop_reason="tool_use"),
        ModelResponse(content=[ToolUseBlock(id="c3", name="mark_ready_for_review", input={})], stop_reason="tool_use"),
        ModelResponse(content=[TextBlock(text="drafted")], stop_reason="end_turn"),
    ])
    app = create_app(model_client=client_stage_1, repo_root=tmp_repo)
    api = TestClient(app)
    api.post("/runs/design/start", json={"brief": "I need a faithfulness eval"})

    run_md_path = tmp_repo / "worksheets" / "design-my-eval" / "RUN.md"
    tampered = run_md_path.read_text(encoding="utf-8").replace("approved_stages: []", 'approved_stages: ["01"]')

    response = api.put("/runs/design-my-eval/files/RUN.md", json={"content": tampered})
    assert response.status_code == 400
    assert "approved_stages" in run_md_path.read_text(encoding="utf-8")
    assert '["01"]' not in run_md_path.read_text(encoding="utf-8")


def test_resolve_run_file_rejects_path_traversal(tmp_repo: Path):
    from app.main import _resolve_run_file

    run_root = tmp_repo / "worksheets" / "design-my-eval"
    run_root.mkdir(parents=True)
    with pytest.raises(HTTPException):
        _resolve_run_file(run_root, "../../CLAUDE.md")


def test_cors_allows_the_vite_dev_origin(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.get("/runs", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
```

`test_api.py` needs `import pytest` added at the top if not already present — check the existing file first; add it if missing.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api.py -v -k "file or cors or traversal"`
Expected: FAIL — `404 Not Found` for the file routes (don't exist yet), `ImportError` or `AttributeError` for `_resolve_run_file`, and a missing CORS header for the CORS test.

- [ ] **Step 3: Implement the endpoints, the traversal guard, and CORS**

In `_server/app/main.py`, add to imports:

```python
from fastapi.middleware.cors import CORSMiddleware
from .run_md import RunMdError, approved_stages_would_change, parse_run_md
```

(Combine with Task 2's `run_md` import into one line as shown.)

Right after `app = FastAPI(title="ecbd-workspace orchestration backend")` in `create_app`, add:

```python
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

Add a module-level helper (outside `create_app`, near `_require_valid_stage`):

```python
def _resolve_run_file(run_root: Path, file_path: str) -> Path:
    target = (run_root / file_path).resolve()
    if not target.is_relative_to(run_root.resolve()):
        raise HTTPException(400, f"'{file_path}' escapes the run folder")
    return target
```

Add a request model near the other `BaseModel` classes:

```python
class FileWriteRequest(BaseModel):
    content: str
```

Add the two routes inside `create_app` (near the diff route):

```python
    @app.get("/runs/{slug}/files/{file_path:path}")
    def get_file(slug: str, file_path: str) -> dict[str, str]:
        run_root = repo_root / "worksheets" / slug
        if not run_root.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        target = _resolve_run_file(run_root, file_path)
        if not target.exists() or not target.is_file():
            raise HTTPException(404, f"'{file_path}' does not exist in run '{slug}'")
        return {"path": file_path, "content": target.read_text(encoding="utf-8")}

    @app.put("/runs/{slug}/files/{file_path:path}")
    def put_file(slug: str, file_path: str, req: FileWriteRequest) -> dict[str, str]:
        run_root = repo_root / "worksheets" / slug
        if not run_root.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        target = _resolve_run_file(run_root, file_path)
        if target.name == "RUN.md":
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            if approved_stages_would_change(current, req.content):
                raise HTTPException(
                    400,
                    "approved_stages in RUN.md can only be changed by approve/reject, not a direct file edit",
                )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(req.content, encoding="utf-8")
        return {"path": file_path, "content": req.content}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/ -v`
Expected: PASS — every test in `_server/tests/`, old and new.

- [ ] **Step 5: Commit**

```bash
git add _server/app/main.py _server/tests/test_api.py
git commit -m "Add GET/PUT /runs/:slug/files/:path and CORS for the frontend dev server

The document viewer/editor endpoint the API design already specified,
scoped to the run folder with a path-traversal guard, and blocked from
ever changing RUN.md's approved_stages -- that stays exclusively
approve_stage/reject_stage's to write. CORS opened for the Vite dev
server origin only.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Part 2 — Frontend

### Task 4: Scaffold the Vite + React + TypeScript + Vitest project

**Files:**
- Create: `_client/` (via `npm create vite`)
- Modify: `_client/src/App.tsx`, `_client/vite.config.ts`, `_client/package.json`
- Create: `_client/src/setupTests.ts`, `_client/src/App.test.tsx`, `_client/CONTEXT.md`, `_client/.env.example`

**Interfaces:**
- Produces: a running `App` component (placeholder, replaced route-by-route in later tasks) and a working `npm test` command every later task's tests run under.

- [ ] **Step 1: Scaffold the project**

Run from the repo root:

```bash
npm create vite@latest _client -- --template react-ts
```

Then install dependencies:

```bash
cd _client
npm install
npm install @tanstack/react-query react-router-dom
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

- [ ] **Step 2: Wire Vitest into `vite.config.ts`**

Replace the generated `_client/vite.config.ts` with:

```typescript
/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/setupTests.ts"],
    globals: true,
  },
});
```

- [ ] **Step 3: Add the test setup file and a `test` script**

Create `_client/src/setupTests.ts`:

```typescript
import "@testing-library/jest-dom/vitest";
```

In `_client/package.json`'s `"scripts"` block, add:

```json
"test": "vitest run"
```

- [ ] **Step 4: Write the failing smoke test**

Create `_client/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("renders the workspace name", () => {
    render(<App />);
    expect(screen.getByText(/ecbd-workspace/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 5: Run the test to verify it fails**

Run (from `_client/`): `npm test`
Expected: FAIL — the default Vite template's `App` doesn't render "ecbd-workspace".

- [ ] **Step 6: Replace `App.tsx` with a minimal placeholder**

Replace `_client/src/App.tsx`:

```tsx
export function App() {
  return <div className="app-shell">ecbd-workspace</div>;
}
```

Delete the generated `_client/src/App.css` (not used) and remove its import from `App.tsx` if the scaffold added one.

- [ ] **Step 7: Run the test to verify it passes**

Run: `npm test`
Expected: PASS.

- [ ] **Step 8: Add `CONTEXT.md` and `.env.example`**

Create `_client/CONTEXT.md`:

```markdown
The frontend for the orchestration backend's web app. Not part of any
pipeline run -- factory, like `_server/` and `_tools/`, not product.

Read `docs/superpowers/specs/2026-09-09-orchestrator-frontend-design.md`
before touching this folder; it covers what this app does and does not
do (no streaming, no session resumption across a backend restart, one
pipeline for now).

Run the dev server from this directory: `npm run dev` (expects the
backend running separately on `http://127.0.0.1:8000` -- see
`_server/CONTEXT.md`). Run tests: `npm test`.

Backend base URL is configurable via `VITE_API_BASE` (see `.env.example`).
```

Create `_client/.env.example`:

```
VITE_API_BASE=http://127.0.0.1:8000
```

- [ ] **Step 9: Commit**

```bash
git add _client/ .gitignore
git commit -m "Scaffold the orchestrator frontend (Vite + React + TypeScript + Vitest)

Empty shell wired for testing; every following task fills in one
route or component at a time against the backend's actual API surface.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

Note: `npm create vite` generates its own `_client/.gitignore` (ignoring `node_modules/`, `dist/`) — leave it as generated.

---

### Task 5: API client — typed `fetch` wrapper and response types

**Files:**
- Create: `_client/src/api/client.ts`, `_client/src/api/types.ts`
- Test: `_client/src/api/client.test.ts`

**Interfaces:**
- Produces (used by every later `api/` and component task):
  - `class ApiError extends Error { status: number }`
  - `const api: { get<T>(path): Promise<T>; post<T>(path, body?): Promise<T>; put<T>(path, body): Promise<T> }`
  - Types: `RunSummary`, `StageTableRow`, `LoopBack`, `RunDetail`, `TranscriptBlock`, `TranscriptEntry`, `SessionState`, `FileContent`, `DiffResponse`, `ApproveResponse` (all in `types.ts`, shown in full below).

- [ ] **Step 1: Write the failing tests**

Create `_client/src/api/client.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "./client";

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed JSON on success", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ hello: "world" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await api.get<{ hello: string }>("/runs");
    expect(result).toEqual({ hello: "world" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/runs"),
      expect.objectContaining({ headers: expect.objectContaining({ "Content-Type": "application/json" }) }),
    );
  });

  it("throws ApiError with the status and body text on failure", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      text: async () => "run 'x' does not exist",
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.get("/runs/x")).rejects.toMatchObject(
      new ApiError(404, "run 'x' does not exist"),
    );
  });

  it("sends a JSON body for post", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);

    await api.post("/runs/design/start", { brief: "hi" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/runs/design/start"),
      expect.objectContaining({ method: "POST", body: JSON.stringify({ brief: "hi" }) }),
    );
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- api/client`
Expected: FAIL — `client.ts` doesn't exist yet.

- [ ] **Step 3: Implement `client.ts` and `types.ts`**

Create `_client/src/api/client.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string): Promise<T> => request<T>(path),
  post: <T>(path: string, body?: unknown): Promise<T> =>
    request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  put: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
};
```

Create `_client/src/api/types.ts`:

```typescript
export interface RunSummary {
  slug: string;
  mode: string;
  subject: string;
  opened: string;
}

export interface StageTableRow {
  file: string;
  stage: string;
  questions: string;
  done: boolean;
}

export interface LoopBack {
  date: string;
  from_stage: string;
  back_to_stage: string;
  forced_by: string;
  what_changed: string;
}

export interface RunDetail {
  slug: string;
  status: string | null;
  opened: string | null;
  closed: string | null;
  approved_stages: string[];
  stages: StageTableRow[];
  loop_backs: LoopBack[];
}

export type TranscriptBlock =
  | { type: "text"; text: string }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; content: string; is_error: boolean };

export interface TranscriptEntry {
  role: "user" | "assistant";
  content: TranscriptBlock[];
}

export interface SessionState {
  transcript: TranscriptEntry[];
  ready_for_review: boolean;
}

export interface FileContent {
  path: string;
  content: string;
}

export interface DiffResponse {
  diff: string;
}

export interface ApproveResponse {
  approved_stage: string;
  approved_outputs: string[];
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- api/client`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/api/client.ts _client/src/api/client.test.ts _client/src/api/types.ts
git commit -m "Add the typed API client and response types

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 6: React Query hooks and session-id persistence

**Files:**
- Create: `_client/src/api/queries.ts`, `_client/src/api/mutations.ts`, `_client/src/lib/sessionStorage.ts`
- Test: `_client/src/api/queries.test.tsx`, `_client/src/lib/sessionStorage.test.ts`
- Modify: `_client/src/main.tsx` (wrap `App` in `QueryClientProvider` + `BrowserRouter`)

**Interfaces:**
- Consumes: `api`, `ApiError` from Task 5's `client.ts`; all types from `types.ts`.
- Produces (used by every page/component task from here on):
  - `useRuns()`, `useRun(slug)`, `useSession(sessionId)`, `useRunFile(slug, path)`, `useStageDiff(slug, stage)` — React Query hooks, query keys `["runs"]`, `["run", slug]`, `["session", sessionId]`, `["file", slug, path]`, `["diff", slug, stage]`.
  - `useStartRun()`, `useStartStage(slug, stage)`, `useSendMessage(sessionId)`, `useApproveStage(slug, stage)`, `useRejectStage(slug, stage)`, `useSaveFile(slug, path)` — mutations, each invalidating the query its action changes.
  - `storeSessionId(runKey, stage, sessionId)`, `loadSessionId(runKey, stage): string | null`, `clearSessionId(runKey, stage)`.

- [ ] **Step 1: Write the failing tests**

Create `_client/src/lib/sessionStorage.test.ts`:

```typescript
import { beforeEach, describe, expect, it, vi } from "vitest";
import { clearSessionId, loadSessionId, storeSessionId } from "./sessionStorage";

describe("sessionStorage helpers", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("round-trips a stored session id", () => {
    storeSessionId("design-my-eval", "02", "abc-123");
    expect(loadSessionId("design-my-eval", "02")).toBe("abc-123");
  });

  it("returns null when nothing is stored", () => {
    expect(loadSessionId("design-my-eval", "03")).toBeNull();
  });

  it("clears a stored session id", () => {
    storeSessionId("design-my-eval", "02", "abc-123");
    clearSessionId("design-my-eval", "02");
    expect(loadSessionId("design-my-eval", "02")).toBeNull();
  });

  it("keeps different (runKey, stage) pairs independent", () => {
    storeSessionId("design-my-eval", "01", "session-a");
    storeSessionId("design-my-eval", "02", "session-b");
    expect(loadSessionId("design-my-eval", "01")).toBe("session-a");
    expect(loadSessionId("design-my-eval", "02")).toBe("session-b");
  });

  it("does not throw when localStorage access fails", () => {
    const spy = vi.spyOn(window.localStorage.__proto__, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(() => storeSessionId("design-my-eval", "01", "x")).not.toThrow();
    spy.mockRestore();
  });
});
```

Create `_client/src/api/queries.test.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useRuns } from "./queries";

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("useRuns", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches the run list from /runs", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ slug: "design-my-eval", mode: "design", subject: "s", opened: "2026-09-09" }],
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useRuns(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([
      { slug: "design-my-eval", mode: "design", subject: "s", opened: "2026-09-09" },
    ]);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/runs"), expect.anything());
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- sessionStorage queries`
Expected: FAIL — neither module exists yet.

- [ ] **Step 3: Implement `sessionStorage.ts`, `queries.ts`, `mutations.ts`**

Create `_client/src/lib/sessionStorage.ts`:

```typescript
const PREFIX = "ecbd-session:";

function key(runKey: string, stage: string): string {
  return `${PREFIX}${runKey}:${stage}`;
}

export function storeSessionId(runKey: string, stage: string, sessionId: string): void {
  try {
    window.localStorage.setItem(key(runKey, stage), sessionId);
  } catch {
    // localStorage unavailable (private mode, disabled) -- the session just won't survive a refresh
  }
}

export function loadSessionId(runKey: string, stage: string): string | null {
  try {
    return window.localStorage.getItem(key(runKey, stage));
  } catch {
    return null;
  }
}

export function clearSessionId(runKey: string, stage: string): void {
  try {
    window.localStorage.removeItem(key(runKey, stage));
  } catch {
    // ignore
  }
}
```

Create `_client/src/api/queries.ts`:

```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { DiffResponse, FileContent, RunDetail, RunSummary, SessionState } from "./types";

export function useRuns() {
  return useQuery({ queryKey: ["runs"], queryFn: () => api.get<RunSummary[]>("/runs") });
}

export function useRun(slug: string | undefined) {
  return useQuery({
    queryKey: ["run", slug],
    queryFn: () => api.get<RunDetail>(`/runs/${slug}`),
    enabled: slug !== undefined,
  });
}

export function useSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => api.get<SessionState>(`/sessions/${sessionId}`),
    enabled: sessionId !== undefined,
    retry: false,
  });
}

export function useRunFile(slug: string | undefined, path: string | undefined) {
  return useQuery({
    queryKey: ["file", slug, path],
    queryFn: () => api.get<FileContent>(`/runs/${slug}/files/${path}`),
    enabled: slug !== undefined && path !== undefined,
  });
}

export function useStageDiff(slug: string | undefined, stage: string | undefined) {
  return useQuery({
    queryKey: ["diff", slug, stage],
    queryFn: () => api.get<DiffResponse>(`/runs/${slug}/diff/${stage}`),
    enabled: slug !== undefined && stage !== undefined,
  });
}
```

Create `_client/src/api/mutations.ts`:

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { ApproveResponse, FileContent } from "./types";

export function useStartRun() {
  return useMutation({
    mutationFn: (brief: string) => api.post<{ session_id: string }>("/runs/design/start", { brief }),
  });
}

export function useStartStage(slug: string, stage: string) {
  return useMutation({
    mutationFn: (brief: string) =>
      api.post<{ session_id: string }>(`/runs/${slug}/stages/${stage}/start`, { brief }),
  });
}

export function useSendMessage(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (brief: string) => api.post<{ reply: string }>(`/sessions/${sessionId}/messages`, { brief }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
    },
  });
}

export function useApproveStage(slug: string, stage: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<ApproveResponse>(`/runs/${slug}/stages/${stage}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", slug] });
    },
  });
}

export function useRejectStage(slug: string, stage: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { target_stage: string; reason: string }) =>
      api.post<{ status: string }>(`/runs/${slug}/stages/${stage}/reject`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", slug] });
    },
  });
}

export function useSaveFile(slug: string, path: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => api.put<FileContent>(`/runs/${slug}/files/${path}`, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["file", slug, path] });
    },
  });
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- sessionStorage queries`
Expected: PASS.

- [ ] **Step 5: Wrap `App` with the providers**

Replace `_client/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
```

- [ ] **Step 6: Run the full test suite to confirm nothing broke**

Run: `npm test`
Expected: PASS (the Task 4 `App.test.tsx` smoke test still renders `App` directly, which doesn't need the providers since it renders no routed/query-consuming content yet).

- [ ] **Step 7: Commit**

```bash
git add _client/src/api/queries.ts _client/src/api/queries.test.tsx _client/src/api/mutations.ts _client/src/lib/sessionStorage.ts _client/src/lib/sessionStorage.test.ts _client/src/main.tsx
git commit -m "Add React Query hooks for every backend endpoint, and session-id persistence

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: `StageRail` component

**Files:**
- Create: `_client/src/components/StageRail.tsx`
- Test: `_client/src/components/StageRail.test.tsx`

**Interfaces:**
- Consumes: `StageTableRow` from `types.ts`.
- Produces: `isStageUnlocked(stages: StageTableRow[], approvedStages: string[], stage: string): boolean` (pure, exported for direct testing) and `<StageRail slug approvedStages stages activeStage />`.

- [ ] **Step 1: Write the failing tests**

Create `_client/src/components/StageRail.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { StageRail, isStageUnlocked } from "./StageRail";
import type { StageTableRow } from "../api/types";

const stages: StageTableRow[] = [
  { file: "01_intended-use.md", stage: "01", questions: "Q1-2", done: true },
  { file: "02_capability.md", stage: "02", questions: "Q3-5", done: false },
  { file: "03_content.md", stage: "03", questions: "Q6-8", done: false },
];

describe("isStageUnlocked", () => {
  it("the first stage is always unlocked", () => {
    expect(isStageUnlocked(stages, [], "01")).toBe(true);
  });

  it("a later stage is locked until every prior stage is approved", () => {
    expect(isStageUnlocked(stages, [], "02")).toBe(false);
    expect(isStageUnlocked(stages, ["01"], "02")).toBe(true);
  });

  it("stage 3 needs both 1 and 2 approved", () => {
    expect(isStageUnlocked(stages, ["01"], "03")).toBe(false);
    expect(isStageUnlocked(stages, ["01", "02"], "03")).toBe(true);
  });
});

describe("StageRail", () => {
  it("renders locked stages as non-links and unlocked stages as links", () => {
    render(
      <MemoryRouter>
        <StageRail slug="design-my-eval" stages={stages} approvedStages={["01"]} activeStage="02" />
      </MemoryRouter>,
    );

    const stage01 = screen.getByRole("link", { name: /01/ });
    expect(stage01).toHaveAttribute("href", "/runs/design-my-eval/stages/01");

    const stage03 = screen.getByText(/03/);
    expect(stage03).toHaveAttribute("aria-disabled", "true");
    expect(screen.queryByRole("link", { name: /03/ })).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- StageRail`
Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Implement `StageRail.tsx`**

```tsx
import { Link } from "react-router-dom";
import type { StageTableRow } from "../api/types";

interface StageRailProps {
  slug: string;
  stages: StageTableRow[];
  approvedStages: string[];
  activeStage: string;
}

export function isStageUnlocked(stages: StageTableRow[], approvedStages: string[], stage: string): boolean {
  const index = stages.findIndex((s) => s.stage === stage);
  if (index <= 0) return true;
  return stages.slice(0, index).every((s) => approvedStages.includes(s.stage));
}

export function StageRail({ slug, stages, approvedStages, activeStage }: StageRailProps) {
  return (
    <nav aria-label="Stage progress" className="stage-rail">
      {stages.map((row) => {
        const unlocked = isStageUnlocked(stages, approvedStages, row.stage);
        const approved = approvedStages.includes(row.stage);
        const isActive = row.stage === activeStage;
        const label = `${row.stage}${approved ? " ✓" : isActive ? " ●" : ""}`;

        if (!unlocked) {
          return (
            <span key={row.stage} className="stage-rail__item stage-rail__item--locked" aria-disabled="true">
              {label}
            </span>
          );
        }
        return (
          <Link
            key={row.stage}
            to={`/runs/${slug}/stages/${row.stage}`}
            className={`stage-rail__item${isActive ? " stage-rail__item--active" : ""}`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- StageRail`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/components/StageRail.tsx _client/src/components/StageRail.test.tsx
git commit -m "Add StageRail: locked/unlocked/approved stage navigation

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 8: `RunSwitcher` component

**Files:**
- Create: `_client/src/components/RunSwitcher.tsx`
- Test: `_client/src/components/RunSwitcher.test.tsx`

**Interfaces:**
- Consumes: `useRuns` from `../api/queries` (mocked in the test via `vi.mock`).
- Produces: `<RunSwitcher currentSlug />`, a `<select>` that navigates to `/runs/{slug}` on change.

- [ ] **Step 1: Write the failing test**

Create `_client/src/components/RunSwitcher.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { RunSwitcher } from "./RunSwitcher";

vi.mock("../api/queries", () => ({
  useRuns: () => ({
    data: [
      { slug: "design-my-eval", mode: "design", subject: "Faithfulness", opened: "2026-09-09" },
      { slug: "design-other", mode: "design", subject: "Other run", opened: "2026-09-08" },
    ],
  }),
}));

function LocationProbe() {
  return null;
}

describe("RunSwitcher", () => {
  it("lists every run and navigates on selection", async () => {
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/01"]}>
        <RunSwitcher currentSlug="design-my-eval" />
        <Routes>
          <Route path="/runs/:slug" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    const select = screen.getByRole("combobox", { name: /switch run/i });
    expect(select).toHaveValue("design-my-eval");
    expect(screen.getByRole("option", { name: /other run/i })).toBeInTheDocument();

    await userEvent.selectOptions(select, "design-other");
    expect(select).toHaveValue("design-other");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `_client/`): `npm test -- RunSwitcher`
Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Implement `RunSwitcher.tsx`**

```tsx
import { useNavigate } from "react-router-dom";
import { useRuns } from "../api/queries";

interface RunSwitcherProps {
  currentSlug: string;
}

export function RunSwitcher({ currentSlug }: RunSwitcherProps) {
  const { data: runs } = useRuns();
  const navigate = useNavigate();

  return (
    <select
      aria-label="Switch run"
      value={currentSlug}
      onChange={(event) => navigate(`/runs/${event.target.value}`)}
    >
      {(runs ?? []).map((run) => (
        <option key={run.slug} value={run.slug}>
          {run.subject || run.slug}
        </option>
      ))}
    </select>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm test -- RunSwitcher`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/components/RunSwitcher.tsx _client/src/components/RunSwitcher.test.tsx
git commit -m "Add RunSwitcher: a dropdown to jump between runs

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 9: `TranscriptView` component

**Files:**
- Create: `_client/src/components/TranscriptView.tsx`
- Test: `_client/src/components/TranscriptView.test.tsx`

**Interfaces:**
- Consumes: `TranscriptEntry` from `types.ts`.
- Produces: `toRenderLines(entries: TranscriptEntry[]): RenderLine[]` (pure, exported) and `<TranscriptView entries />`.

- [ ] **Step 1: Write the failing tests**

Create `_client/src/components/TranscriptView.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TranscriptView, toRenderLines } from "./TranscriptView";
import type { TranscriptEntry } from "../api/types";

const entries: TranscriptEntry[] = [
  { role: "user", content: [{ type: "text", text: "let's start" }] },
  {
    role: "assistant",
    content: [
      { type: "tool_use", id: "t1", name: "write_file", input: { path: "01_intended-use.md", content: "..." } },
    ],
  },
  {
    role: "user",
    content: [{ type: "tool_result", tool_use_id: "t1", content: "wrote 01_intended-use.md", is_error: false }],
  },
  {
    role: "assistant",
    content: [{ type: "tool_use", id: "t2", name: "read_file", input: { path: "does-not-exist.md" } }],
  },
  {
    role: "user",
    content: [{ type: "tool_result", tool_use_id: "t2", content: "'does-not-exist.md' does not exist", is_error: true }],
  },
  { role: "assistant", content: [{ type: "text", text: "drafted, ready for review" }] },
];

describe("toRenderLines", () => {
  it("pairs tool_use with its tool_result and keeps text lines separate", () => {
    const lines = toRenderLines(entries);
    expect(lines).toEqual([
      { kind: "text", role: "user", text: "let's start" },
      {
        kind: "tool",
        name: "write_file",
        input: { path: "01_intended-use.md", content: "..." },
        result: "wrote 01_intended-use.md",
        isError: false,
      },
      {
        kind: "tool",
        name: "read_file",
        input: { path: "does-not-exist.md" },
        result: "'does-not-exist.md' does not exist",
        isError: true,
      },
      { kind: "text", role: "assistant", text: "drafted, ready for review" },
    ]);
  });
});

describe("TranscriptView", () => {
  it("flags an error tool result distinctly", () => {
    render(<TranscriptView entries={entries} />);
    const errorLine = screen.getByText(/read_file/).closest("details");
    expect(errorLine).toHaveClass("transcript__activity--error");

    const okLine = screen.getByText(/write_file/).closest("details");
    expect(okLine).not.toHaveClass("transcript__activity--error");
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- TranscriptView`
Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Implement `TranscriptView.tsx`**

```tsx
import type { TranscriptEntry } from "../api/types";

interface TranscriptViewProps {
  entries: TranscriptEntry[];
}

interface TextLine {
  kind: "text";
  role: "user" | "assistant";
  text: string;
}

interface ToolLine {
  kind: "tool";
  name: string;
  input: Record<string, unknown>;
  result: string;
  isError: boolean;
}

export type RenderLine = TextLine | ToolLine;

export function toRenderLines(entries: TranscriptEntry[]): RenderLine[] {
  const lines: RenderLine[] = [];
  const pendingToolUse = new Map<string, { name: string; input: Record<string, unknown> }>();

  for (const entry of entries) {
    for (const block of entry.content) {
      if (block.type === "text") {
        lines.push({ kind: "text", role: entry.role, text: block.text });
      } else if (block.type === "tool_use") {
        pendingToolUse.set(block.id, { name: block.name, input: block.input });
      } else if (block.type === "tool_result") {
        const use = pendingToolUse.get(block.tool_use_id);
        lines.push({
          kind: "tool",
          name: use?.name ?? "unknown tool",
          input: use?.input ?? {},
          result: block.content,
          isError: block.is_error,
        });
        pendingToolUse.delete(block.tool_use_id);
      }
    }
  }
  return lines;
}

function toolIcon(name: string): string {
  if (name === "write_file" || name === "edit_file") return "📝";
  if (name === "read_file") return "📖";
  if (name === "create_run") return "🗂️";
  if (name === "mark_ready_for_review") return "✅";
  return "🔧";
}

export function TranscriptView({ entries }: TranscriptViewProps) {
  const lines = toRenderLines(entries);
  return (
    <div className="transcript">
      {lines.map((line, index) => {
        if (line.kind === "text") {
          return (
            <p key={index} className={`transcript__bubble transcript__bubble--${line.role}`}>
              {line.text}
            </p>
          );
        }
        const path = typeof line.input.path === "string" ? line.input.path : undefined;
        return (
          <details
            key={index}
            className={`transcript__activity${line.isError ? " transcript__activity--error" : ""}`}
          >
            <summary>
              {toolIcon(line.name)} {line.name}
              {path ? ` \`${path}\`` : ""}
            </summary>
            <pre>{line.result}</pre>
          </details>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- TranscriptView`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/components/TranscriptView.tsx _client/src/components/TranscriptView.test.tsx
git commit -m "Add TranscriptView: collapsible tool activity, error lines flagged

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 10: `DiffView` and `ReviewBanner` components

**Files:**
- Create: `_client/src/components/DiffView.tsx`, `_client/src/components/ReviewBanner.tsx`
- Test: `_client/src/components/DiffView.test.tsx`, `_client/src/components/ReviewBanner.test.tsx`

**Interfaces:**
- Produces: `<DiffView diff={string} />`, `<ReviewBanner onViewDiff onApprove onReject approving />`.

- [ ] **Step 1: Write the failing tests**

Create `_client/src/components/DiffView.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DiffView } from "./DiffView";

const sampleDiff = [
  "--- 01_intended-use.md (session start)",
  "+++ 01_intended-use.md (current)",
  "@@ -0,0 +1 @@",
  "+the intended use, spelled out",
].join("\n");

describe("DiffView", () => {
  it("marks added lines and leaves headers unmarked", () => {
    render(<DiffView diff={sampleDiff} />);
    const added = screen.getByText("+the intended use, spelled out");
    expect(added).toHaveClass("diff-view__line--added");

    const header = screen.getByText("+++ 01_intended-use.md (current)");
    expect(header).not.toHaveClass("diff-view__line--added");
  });
});
```

Create `_client/src/components/ReviewBanner.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ReviewBanner } from "./ReviewBanner";

describe("ReviewBanner", () => {
  it("calls the right handler for each action", async () => {
    const onViewDiff = vi.fn();
    const onApprove = vi.fn();
    const onReject = vi.fn();
    render(<ReviewBanner onViewDiff={onViewDiff} onApprove={onApprove} onReject={onReject} approving={false} />);

    await userEvent.click(screen.getByRole("button", { name: /view diff/i }));
    await userEvent.click(screen.getByRole("button", { name: /^approve$/i }));
    await userEvent.click(screen.getByRole("button", { name: /reject/i }));

    expect(onViewDiff).toHaveBeenCalledOnce();
    expect(onApprove).toHaveBeenCalledOnce();
    expect(onReject).toHaveBeenCalledOnce();
  });

  it("disables Approve and shows progress while approving", () => {
    render(<ReviewBanner onViewDiff={vi.fn()} onApprove={vi.fn()} onReject={vi.fn()} approving={true} />);
    expect(screen.getByRole("button", { name: /approving/i })).toBeDisabled();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- DiffView ReviewBanner`
Expected: FAIL — neither module exists.

- [ ] **Step 3: Implement both components**

Create `_client/src/components/DiffView.tsx`:

```tsx
interface DiffViewProps {
  diff: string;
}

export function DiffView({ diff }: DiffViewProps) {
  const lines = diff.split("\n");
  return (
    <pre className="diff-view">
      {lines.map((line, index) => {
        let className = "diff-view__line";
        if (line.startsWith("+") && !line.startsWith("+++")) className += " diff-view__line--added";
        else if (line.startsWith("-") && !line.startsWith("---")) className += " diff-view__line--removed";
        return (
          <div key={index} className={className}>
            {line}
          </div>
        );
      })}
    </pre>
  );
}
```

Create `_client/src/components/ReviewBanner.tsx`:

```tsx
interface ReviewBannerProps {
  onViewDiff: () => void;
  onApprove: () => void;
  onReject: () => void;
  approving: boolean;
}

export function ReviewBanner({ onViewDiff, onApprove, onReject, approving }: ReviewBannerProps) {
  return (
    <div role="status" className="review-banner">
      <span>✓ Ready for review — model marked this draft done.</span>
      <button onClick={onViewDiff}>View diff</button>
      <button onClick={onApprove} disabled={approving}>
        {approving ? "Approving…" : "Approve"}
      </button>
      <button onClick={onReject}>Reject…</button>
    </div>
  );
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- DiffView ReviewBanner`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/components/DiffView.tsx _client/src/components/DiffView.test.tsx _client/src/components/ReviewBanner.tsx _client/src/components/ReviewBanner.test.tsx
git commit -m "Add DiffView and ReviewBanner for the human-check gate

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 11: `RejectDialog` component

**Files:**
- Create: `_client/src/components/RejectDialog.tsx`
- Test: `_client/src/components/RejectDialog.test.tsx`

**Interfaces:**
- Produces: `<RejectDialog approvedStages currentStage onSubmit onCancel />`, calling `onSubmit({ target_stage, reason })`.

- [ ] **Step 1: Write the failing test**

Create `_client/src/components/RejectDialog.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RejectDialog } from "./RejectDialog";

describe("RejectDialog", () => {
  it("submits the chosen target stage and typed reason, excluding the current stage from choices", async () => {
    const onSubmit = vi.fn();
    render(
      <RejectDialog
        approvedStages={["01", "02"]}
        currentStage="02"
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.queryByRole("option", { name: "02" })).not.toBeInTheDocument();
    expect(screen.getByRole("option", { name: "01" })).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/reason/i), "intended use was too vague");
    await userEvent.click(screen.getByRole("button", { name: /^reject$/i }));

    expect(onSubmit).toHaveBeenCalledWith({ target_stage: "01", reason: "intended use was too vague" });
  });

  it("disables Reject until a reason is typed", () => {
    render(
      <RejectDialog approvedStages={["01"]} currentStage="02" onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: /^reject$/i })).toBeDisabled();
  });

  it("calls onCancel when Cancel is clicked", async () => {
    const onCancel = vi.fn();
    render(
      <RejectDialog approvedStages={["01"]} currentStage="02" onSubmit={vi.fn()} onCancel={onCancel} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `_client/`): `npm test -- RejectDialog`
Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Implement `RejectDialog.tsx`**

```tsx
import { useState } from "react";

interface RejectDialogProps {
  approvedStages: string[];
  currentStage: string;
  onSubmit: (input: { target_stage: string; reason: string }) => void;
  onCancel: () => void;
}

export function RejectDialog({ approvedStages, currentStage, onSubmit, onCancel }: RejectDialogProps) {
  const candidates = approvedStages.filter((stage) => stage !== currentStage);
  const [targetStage, setTargetStage] = useState(candidates[0] ?? "");
  const [reason, setReason] = useState("");

  return (
    <div role="dialog" aria-label="Reject stage">
      <label>
        Send back to
        <select value={targetStage} onChange={(event) => setTargetStage(event.target.value)}>
          {candidates.map((stage) => (
            <option key={stage} value={stage}>
              {stage}
            </option>
          ))}
        </select>
      </label>
      <label>
        Reason
        <textarea value={reason} onChange={(event) => setReason(event.target.value)} />
      </label>
      <button
        onClick={() => onSubmit({ target_stage: targetStage, reason })}
        disabled={!targetStage || !reason.trim()}
      >
        Reject
      </button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm test -- RejectDialog`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/components/RejectDialog.tsx _client/src/components/RejectDialog.test.tsx
git commit -m "Add RejectDialog: pick a target stage from those already approved

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 12: `ChatDrawer` component

**Files:**
- Create: `_client/src/components/ChatDrawer.tsx`
- Test: `_client/src/components/ChatDrawer.test.tsx`

**Interfaces:**
- Consumes: `useSession` from `../api/queries`, `useSendMessage` from `../api/mutations`, `loadSessionId`/`storeSessionId`/`clearSessionId` from `../lib/sessionStorage`, `ApiError` from `../api/client`, `TranscriptView` from `./TranscriptView` (all mocked in the test).
- Produces: `<ChatDrawer runKey stage startSession onSessionId? />` — `startSession: (brief: string) => Promise<{ session_id: string }>` is passed in by the parent page, since the two callers (new-run bootstrap vs. an existing stage) hit different endpoints.

- [ ] **Step 1: Write the failing tests**

Create `_client/src/components/ChatDrawer.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ChatDrawer } from "./ChatDrawer";
import { ApiError } from "../api/client";

const mockLoadSessionId = vi.fn();
const mockStoreSessionId = vi.fn();
const mockClearSessionId = vi.fn();
vi.mock("../lib/sessionStorage", () => ({
  loadSessionId: (...args: unknown[]) => mockLoadSessionId(...args),
  storeSessionId: (...args: unknown[]) => mockStoreSessionId(...args),
  clearSessionId: (...args: unknown[]) => mockClearSessionId(...args),
}));

const mockUseSession = vi.fn();
vi.mock("../api/queries", () => ({
  useSession: (...args: unknown[]) => mockUseSession(...args),
}));

const mockMutateAsync = vi.fn();
vi.mock("../api/mutations", () => ({
  useSendMessage: () => ({ mutateAsync: mockMutateAsync, isPending: false, isError: false, error: null }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockUseSession.mockReturnValue({ data: undefined, isError: false, error: null });
});

describe("ChatDrawer", () => {
  it("shows a start form when no session exists yet, and starts one", async () => {
    mockLoadSessionId.mockReturnValue(null);
    const startSession = vi.fn().mockResolvedValue({ session_id: "sess-1" });

    render(<ChatDrawer runKey="new" stage="01" startSession={startSession} />);

    await userEvent.type(screen.getByPlaceholderText(/say what you need/i), "I need a faithfulness eval");
    await userEvent.click(screen.getByRole("button", { name: /^start$/i }));

    expect(startSession).toHaveBeenCalledWith("I need a faithfulness eval");
    expect(mockStoreSessionId).toHaveBeenCalledWith("new", "01", "sess-1");
  });

  it("shows the transcript and a send form once a session exists", () => {
    mockLoadSessionId.mockReturnValue("sess-1");
    mockUseSession.mockReturnValue({
      data: { transcript: [{ role: "user", content: [{ type: "text", text: "hi" }] }], ready_for_review: false },
      isError: false,
      error: null,
    });

    render(<ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} />);
    userEvent.click(screen.getByRole("button", { name: /expand chat/i }));
  });

  it("offers to start over when the stored session is gone (404)", () => {
    mockLoadSessionId.mockReturnValue("sess-stale");
    mockUseSession.mockReturnValue({ data: undefined, isError: true, error: new ApiError(404, "no such session") });

    render(<ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/no longer available/i);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- ChatDrawer`
Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Implement `ChatDrawer.tsx`**

```tsx
import { useState } from "react";
import { useSendMessage } from "../api/mutations";
import { useSession } from "../api/queries";
import { ApiError } from "../api/client";
import { clearSessionId, loadSessionId, storeSessionId } from "../lib/sessionStorage";
import { TranscriptView } from "./TranscriptView";

interface ChatDrawerProps {
  runKey: string;
  stage: string;
  startSession: (brief: string) => Promise<{ session_id: string }>;
  onSessionId?: (sessionId: string) => void;
}

export function ChatDrawer({ runKey, stage, startSession, onSessionId }: ChatDrawerProps) {
  const [sessionId, setSessionId] = useState<string | null>(() => loadSessionId(runKey, stage));
  const [collapsed, setCollapsed] = useState(true);
  const [draft, setDraft] = useState("");
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  const session = useSession(sessionId ?? undefined);
  const sendMessage = useSendMessage(sessionId ?? "");

  const sessionGone = session.isError && session.error instanceof ApiError && session.error.status === 404;

  async function handleStart() {
    setStarting(true);
    setStartError(null);
    try {
      const { session_id } = await startSession(draft);
      storeSessionId(runKey, stage, session_id);
      setSessionId(session_id);
      setDraft("");
      setCollapsed(false);
      onSessionId?.(session_id);
    } catch (err) {
      setStartError(err instanceof Error ? err.message : "failed to start session");
    } finally {
      setStarting(false);
    }
  }

  async function handleSend() {
    if (!draft.trim()) return;
    await sendMessage.mutateAsync(draft);
    setDraft("");
  }

  function handleForget() {
    clearSessionId(runKey, stage);
    setSessionId(null);
  }

  if (sessionId === null || sessionGone) {
    return (
      <div className="chat-drawer chat-drawer--empty">
        {sessionGone && <p role="alert">Previous session is no longer available — start a new one.</p>}
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Say what you need for this stage..."
        />
        <button onClick={handleStart} disabled={starting || !draft.trim()}>
          {starting ? "Starting…" : "Start"}
        </button>
        {startError && <p role="alert">{startError}</p>}
      </div>
    );
  }

  return (
    <div className={`chat-drawer${collapsed ? " chat-drawer--collapsed" : ""}`}>
      <button onClick={() => setCollapsed((c) => !c)}>{collapsed ? "💬 Expand chat" : "Collapse chat"}</button>
      {!collapsed && (
        <>
          {session.data && <TranscriptView entries={session.data.transcript} />}
          <textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Reply..." />
          <button onClick={handleSend} disabled={sendMessage.isPending || !draft.trim()}>
            {sendMessage.isPending ? "Thinking…" : "Send"}
          </button>
          {sendMessage.isError && (
            <p role="alert">{sendMessage.error instanceof Error ? sendMessage.error.message : "send failed"}</p>
          )}
          <button onClick={handleForget}>Forget session</button>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- ChatDrawer`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/components/ChatDrawer.tsx _client/src/components/ChatDrawer.test.tsx
git commit -m "Add ChatDrawer: start/resume a stage session, send messages, surface a gone session

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 13: `DocumentPane` component

**Files:**
- Create: `_client/src/components/DocumentPane.tsx`
- Test: `_client/src/components/DocumentPane.test.tsx`

**Interfaces:**
- Consumes: `useRunFile` from `../api/queries`, `useSaveFile` from `../api/mutations` (both mocked).
- Produces: `<DocumentPane slug file />`.

- [ ] **Step 1: Write the failing tests**

Create `_client/src/components/DocumentPane.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { DocumentPane } from "./DocumentPane";

const mockUseRunFile = vi.fn();
vi.mock("../api/queries", () => ({
  useRunFile: (...args: unknown[]) => mockUseRunFile(...args),
}));

const mockMutate = vi.fn();
vi.mock("../api/mutations", () => ({
  useSaveFile: () => ({ mutate: mockMutate, isPending: false }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("DocumentPane", () => {
  it("shows a folder notice instead of a textarea for a directory output", () => {
    render(<DocumentPane slug="design-my-eval" file="build/" />);
    expect(screen.getByText(/no single-file viewer yet/i)).toBeInTheDocument();
  });

  it("loads content into an editable textarea and enables Save once edited", async () => {
    mockUseRunFile.mockReturnValue({
      data: { path: "01_intended-use.md", content: "original text" },
      isLoading: false,
      isError: false,
    });

    render(<DocumentPane slug="design-my-eval" file="01_intended-use.md" />);
    const textarea = screen.getByDisplayValue("original text");
    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();

    await userEvent.type(textarea, " and more");
    expect(screen.getByRole("button", { name: /save/i })).toBeEnabled();

    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(mockMutate).toHaveBeenCalledWith("original text and more", expect.anything());
  });

  it("shows an error state when the file fails to load", () => {
    mockUseRunFile.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    render(<DocumentPane slug="design-my-eval" file="01_intended-use.md" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- DocumentPane`
Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Implement `DocumentPane.tsx`**

```tsx
import { useEffect, useState } from "react";
import { useRunFile } from "../api/queries";
import { useSaveFile } from "../api/mutations";

interface DocumentPaneProps {
  slug: string;
  file: string;
}

export function DocumentPane({ slug, file }: DocumentPaneProps) {
  const isDirectory = file.endsWith("/");
  const query = useRunFile(slug, isDirectory ? undefined : file);
  const save = useSaveFile(slug, file);
  const [draft, setDraft] = useState("");
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (query.data && !dirty) {
      setDraft(query.data.content);
    }
  }, [query.data, dirty]);

  if (isDirectory) {
    return (
      <p className="document-pane__notice">
        This stage's output is a folder ({file}) — no single-file viewer yet.
      </p>
    );
  }

  if (query.isLoading) return <p>Loading {file}...</p>;
  if (query.isError) return <p role="alert">Could not load {file}.</p>;

  return (
    <div className="document-pane">
      <div className="document-pane__label">{file}</div>
      <textarea
        value={draft}
        onChange={(event) => {
          setDraft(event.target.value);
          setDirty(true);
        }}
      />
      <button
        onClick={() => save.mutate(draft, { onSuccess: () => setDirty(false) })}
        disabled={!dirty || save.isPending}
      >
        {save.isPending ? "Saving…" : "Save"}
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- DocumentPane`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/components/DocumentPane.tsx _client/src/components/DocumentPane.test.tsx
git commit -m "Add DocumentPane: view and edit a stage's output file directly

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 14: `RunListPage`

**Files:**
- Create: `_client/src/pages/RunListPage.tsx`
- Test: `_client/src/pages/RunListPage.test.tsx`

**Interfaces:**
- Consumes: `useRuns` from `../api/queries` (mocked).
- Produces: `<RunListPage />`.

- [ ] **Step 1: Write the failing tests**

Create `_client/src/pages/RunListPage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { RunListPage } from "./RunListPage";

const mockUseRuns = vi.fn();
vi.mock("../api/queries", () => ({
  useRuns: () => mockUseRuns(),
}));

describe("RunListPage", () => {
  it("lists runs with a link to each, and a New run link", () => {
    mockUseRuns.mockReturnValue({
      data: [{ slug: "design-my-eval", mode: "design", subject: "Faithfulness", opened: "2026-09-09" }],
      isLoading: false,
      isError: false,
    });

    render(
      <MemoryRouter>
        <RunListPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "design-my-eval" })).toHaveAttribute(
      "href",
      "/runs/design-my-eval",
    );
    expect(screen.getByRole("link", { name: /new run/i })).toHaveAttribute("href", "/runs/new");
  });

  it("shows an error state when the run list fails to load", () => {
    mockUseRuns.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    render(
      <MemoryRouter>
        <RunListPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- RunListPage`
Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Implement `RunListPage.tsx`**

```tsx
import { Link } from "react-router-dom";
import { useRuns } from "../api/queries";

export function RunListPage() {
  const { data: runs, isLoading, isError } = useRuns();

  if (isLoading) return <p>Loading runs…</p>;
  if (isError) return <p role="alert">Could not load the run list.</p>;

  return (
    <div className="run-list">
      <h1>Runs</h1>
      <Link to="/runs/new">New run</Link>
      <table>
        <thead>
          <tr>
            <th>Slug</th>
            <th>Mode</th>
            <th>Subject</th>
            <th>Opened</th>
          </tr>
        </thead>
        <tbody>
          {(runs ?? []).map((run) => (
            <tr key={run.slug}>
              <td>
                <Link to={`/runs/${run.slug}`}>{run.slug}</Link>
              </td>
              <td>{run.mode}</td>
              <td>{run.subject}</td>
              <td>{run.opened}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- RunListPage`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/pages/RunListPage.tsx _client/src/pages/RunListPage.test.tsx
git commit -m "Add RunListPage

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 15: `NewRunPage`

**Files:**
- Create: `_client/src/pages/NewRunPage.tsx`
- Test: `_client/src/pages/NewRunPage.test.tsx`

**Interfaces:**
- Consumes: `useRuns` from `../api/queries`, `useStartRun` from `../api/mutations`, `api` from `../api/client`, `storeSessionId` from `../lib/sessionStorage`, `ChatDrawer` from `../components/ChatDrawer` (all mocked).
- Produces: `<NewRunPage />` — since `create_run` fires mid-conversation, this page starts a bootstrap chat and offers a "Check for created run" action that polls `/runs` once per click and navigates to the new run once it appears.

- [ ] **Step 1: Write the failing tests**

Create `_client/src/pages/NewRunPage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { NewRunPage } from "./NewRunPage";

const mockUseRuns = vi.fn();
vi.mock("../api/queries", () => ({
  useRuns: () => mockUseRuns(),
}));

const mockMutateAsync = vi.fn();
vi.mock("../api/mutations", () => ({
  useStartRun: () => ({ mutateAsync: mockMutateAsync }),
}));

const mockApiGet = vi.fn();
vi.mock("../api/client", () => ({
  api: { get: (...args: unknown[]) => mockApiGet(...args) },
}));

const mockStoreSessionId = vi.fn();
vi.mock("../lib/sessionStorage", () => ({
  storeSessionId: (...args: unknown[]) => mockStoreSessionId(...args),
}));

vi.mock("../components/ChatDrawer", () => ({
  ChatDrawer: ({ onSessionId }: { onSessionId?: (id: string) => void }) => (
    <button onClick={() => onSessionId?.("sess-new")}>simulate session start</button>
  ),
}));

function LandingProbe() {
  return <p>landed on the new run's stage page</p>;
}

beforeEach(() => {
  vi.clearAllMocks();
  mockUseRuns.mockReturnValue({ data: [] });
});

describe("NewRunPage", () => {
  it("offers Check for created run only after a session has started, and navigates once a new slug appears", async () => {
    render(
      <MemoryRouter initialEntries={["/runs/new"]}>
        <Routes>
          <Route path="/runs/new" element={<NewRunPage />} />
          <Route path="/runs/:slug/stages/:stage" element={<LandingProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.queryByRole("button", { name: /check for created run/i })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /simulate session start/i }));
    expect(screen.getByRole("button", { name: /check for created run/i })).toBeInTheDocument();

    mockApiGet.mockResolvedValue([{ slug: "design-my-eval", mode: "design", subject: "s", opened: "2026-09-09" }]);
    await userEvent.click(screen.getByRole("button", { name: /check for created run/i }));

    expect(mockStoreSessionId).toHaveBeenCalledWith("design-my-eval", "01", "sess-new");
    expect(await screen.findByText(/landed on the new run's stage page/i)).toBeInTheDocument();
  });

  it("reports when no new run has appeared yet", async () => {
    render(
      <MemoryRouter initialEntries={["/runs/new"]}>
        <Routes>
          <Route path="/runs/new" element={<NewRunPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByRole("button", { name: /simulate session start/i }));
    mockApiGet.mockResolvedValue([]);
    await userEvent.click(screen.getByRole("button", { name: /check for created run/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/no new run yet/i);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- NewRunPage`
Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Implement `NewRunPage.tsx`**

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRuns } from "../api/queries";
import { useStartRun } from "../api/mutations";
import { api } from "../api/client";
import type { RunSummary } from "../api/types";
import { ChatDrawer } from "../components/ChatDrawer";
import { storeSessionId } from "../lib/sessionStorage";

export function NewRunPage() {
  const { data: runsBeforeStart } = useRuns();
  const startRun = useStartRun();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [knownSlugs, setKnownSlugs] = useState<Set<string>>(new Set());
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);
  const navigate = useNavigate();

  function handleSessionStarted(id: string) {
    setSessionId(id);
    setKnownSlugs(new Set((runsBeforeStart ?? []).map((run) => run.slug)));
  }

  async function checkForNewRun() {
    if (!sessionId) return;
    setChecking(true);
    setCheckError(null);
    try {
      const runs = await api.get<RunSummary[]>("/runs");
      const created = runs.find((run) => !knownSlugs.has(run.slug));
      if (created) {
        storeSessionId(created.slug, "01", sessionId);
        navigate(`/runs/${created.slug}/stages/01`);
      } else {
        setCheckError("No new run yet — keep chatting, then check again once it's created.");
      }
    } finally {
      setChecking(false);
    }
  }

  return (
    <div className="new-run-page">
      <h1>Start a design run</h1>
      <p>Pipeline: design (the only one supported today)</p>
      <ChatDrawer runKey="new" stage="01" startSession={(brief) => startRun.mutateAsync(brief)} onSessionId={handleSessionStarted} />
      {sessionId && (
        <div>
          <button onClick={checkForNewRun} disabled={checking}>
            {checking ? "Checking…" : "Check for created run"}
          </button>
          {checkError && <p role="alert">{checkError}</p>}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- NewRunPage`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _client/src/pages/NewRunPage.tsx _client/src/pages/NewRunPage.test.tsx
git commit -m "Add NewRunPage: bootstrap chat plus a manual check for the run it creates

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 16: `StagePage` and app routing

**Files:**
- Create: `_client/src/pages/StagePage.tsx`
- Modify: `_client/src/App.tsx`
- Test: `_client/src/pages/StagePage.test.tsx`, `_client/src/App.test.tsx` (extend)

**Interfaces:**
- Consumes every component and hook from Tasks 5-15.
- Produces: `<StagePage />` (reads `:slug`/`:stage` from the route) and the final `App` with all four routes wired (`/`, `/runs/new`, `/runs/:slug` → redirect, `/runs/:slug/stages/:stage`).

- [ ] **Step 1: Write the failing tests**

Create `_client/src/pages/StagePage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { StagePage } from "./StagePage";

const mockUseRun = vi.fn();
const mockUseSession = vi.fn();
vi.mock("../api/queries", () => ({
  useRun: (...args: unknown[]) => mockUseRun(...args),
  useSession: (...args: unknown[]) => mockUseSession(...args),
  useStageDiff: () => ({ data: undefined }),
  useRuns: () => ({ data: [] }),
  useRunFile: () => ({ data: undefined, isLoading: true, isError: false }),
}));

vi.mock("../api/mutations", () => ({
  useStartStage: () => ({ mutateAsync: vi.fn() }),
  useApproveStage: () => ({ mutate: vi.fn(), isPending: false }),
  useRejectStage: () => ({ mutate: vi.fn() }),
  useSaveFile: () => ({ mutate: vi.fn(), isPending: false }),
  // StagePage renders the real ChatDrawer (not mocked), which calls
  // useSendMessage -- must be provided here too or that call throws.
  useSendMessage: () => ({ mutateAsync: vi.fn(), isPending: false, isError: false, error: null }),
}));

vi.mock("../lib/sessionStorage", () => ({
  loadSessionId: () => null,
  storeSessionId: vi.fn(),
  clearSessionId: vi.fn(),
}));

const runDetail = {
  slug: "design-my-eval",
  status: "in-progress",
  opened: "2026-09-09",
  closed: null,
  approved_stages: ["01"],
  stages: [
    { file: "01_intended-use.md", stage: "01", questions: "Q1-2", done: true },
    { file: "02_capability.md", stage: "02", questions: "Q3-5", done: false },
  ],
  loop_backs: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  mockUseRun.mockReturnValue({ data: runDetail, isLoading: false, isError: false });
  mockUseSession.mockReturnValue({ data: undefined, isError: false, error: null });
});

describe("StagePage", () => {
  it("renders the stage rail and the current stage's document, but no review banner when not ready", () => {
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("navigation", { name: /stage progress/i })).toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("shows the review banner once the session reports ready_for_review", () => {
    mockUseSession.mockReturnValue({
      data: { transcript: [], ready_for_review: true },
      isError: false,
      error: null,
    });

    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows an error state when the run fails to load", () => {
    mockUseRun.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
```

Extend `_client/src/App.test.tsx` (replace its contents entirely — `App` is now a router, not a standalone placeholder). This test mocks the **page** components rather than hooks: each page already gets full coverage in its own test file (Tasks 14-16), so `App`'s test only needs to prove routing picks the right page, without dragging in every hook a mocked-out page's children (like `NewRunPage`'s real `ChatDrawer`) would otherwise need mocked too:

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { App } from "./App";

vi.mock("./pages/RunListPage", () => ({ RunListPage: () => <div>run-list-page</div> }));
vi.mock("./pages/NewRunPage", () => ({ NewRunPage: () => <div>new-run-page</div> }));
vi.mock("./pages/StagePage", () => ({ StagePage: () => <div>stage-page</div> }));

const mockUseRun = vi.fn();
vi.mock("./api/queries", () => ({
  useRun: (...args: unknown[]) => mockUseRun(...args),
}));

function renderApp(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <App />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("App routing", () => {
  it("renders the run list at /", () => {
    renderApp("/");
    expect(screen.getByText("run-list-page")).toBeInTheDocument();
  });

  it("renders the new-run page at /runs/new", () => {
    renderApp("/runs/new");
    expect(screen.getByText("new-run-page")).toBeInTheDocument();
  });

  it("renders the stage page directly at /runs/:slug/stages/:stage", () => {
    renderApp("/runs/design-my-eval/stages/02");
    expect(screen.getByText("stage-page")).toBeInTheDocument();
  });

  it("redirects /runs/:slug to the run's current (first non-approved) stage", () => {
    mockUseRun.mockReturnValue({
      data: {
        slug: "design-my-eval",
        approved_stages: ["01"],
        stages: [
          { file: "01_intended-use.md", stage: "01", questions: "", done: true },
          { file: "02_capability.md", stage: "02", questions: "", done: false },
        ],
      },
      isLoading: false,
      isError: false,
    });
    renderApp("/runs/design-my-eval");
    expect(screen.getByText("stage-page")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `_client/`): `npm test -- StagePage App`
Expected: FAIL — `StagePage` doesn't exist yet, and `App` doesn't render routes yet (still the Task 4 placeholder).

- [ ] **Step 3: Implement `StagePage.tsx` and the final `App.tsx`**

Create `_client/src/pages/StagePage.tsx`:

```tsx
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useRun, useSession, useStageDiff } from "../api/queries";
import { useApproveStage, useRejectStage, useStartStage } from "../api/mutations";
import { StageRail } from "../components/StageRail";
import { RunSwitcher } from "../components/RunSwitcher";
import { DocumentPane } from "../components/DocumentPane";
import { ReviewBanner } from "../components/ReviewBanner";
import { DiffView } from "../components/DiffView";
import { RejectDialog } from "../components/RejectDialog";
import { ChatDrawer } from "../components/ChatDrawer";
import { loadSessionId } from "../lib/sessionStorage";

export function StagePage() {
  const { slug, stage } = useParams<{ slug: string; stage: string }>();
  const [showDiff, setShowDiff] = useState(false);
  const [showReject, setShowReject] = useState(false);

  const run = useRun(slug);
  const startStage = useStartStage(slug ?? "", stage ?? "");
  const approve = useApproveStage(slug ?? "", stage ?? "");
  const reject = useRejectStage(slug ?? "", stage ?? "");

  const sessionId = slug && stage ? loadSessionId(slug, stage) : null;
  const session = useSession(sessionId ?? undefined);
  const diff = useStageDiff(showDiff ? slug : undefined, showDiff ? stage : undefined);

  if (!slug || !stage) return null;
  if (run.isLoading) return <p>Loading run…</p>;
  if (run.isError || !run.data) return <p role="alert">Could not load run '{slug}'.</p>;

  const currentRow = run.data.stages.find((row) => row.stage === stage);
  const readyForReview = session.data?.ready_for_review ?? false;

  return (
    <div className="stage-page">
      <header className="stage-page__header">
        <RunSwitcher currentSlug={slug} />
        <span>
          {run.data.slug} | stage {stage}
        </span>
      </header>
      <div className="stage-page__body">
        <StageRail slug={slug} stages={run.data.stages} approvedStages={run.data.approved_stages} activeStage={stage} />
        <main className="stage-page__document">
          {readyForReview && (
            <ReviewBanner
              onViewDiff={() => setShowDiff(true)}
              onApprove={() => approve.mutate()}
              onReject={() => setShowReject(true)}
              approving={approve.isPending}
            />
          )}
          {showDiff && diff.data && <DiffView diff={diff.data.diff} />}
          {showReject && (
            <RejectDialog
              approvedStages={run.data.approved_stages}
              currentStage={stage}
              onSubmit={(input) => reject.mutate(input, { onSuccess: () => setShowReject(false) })}
              onCancel={() => setShowReject(false)}
            />
          )}
          {currentRow && <DocumentPane slug={slug} file={currentRow.file} />}
        </main>
      </div>
      <ChatDrawer runKey={slug} stage={stage} startSession={(brief) => startStage.mutateAsync(brief)} />
    </div>
  );
}
```

Replace `_client/src/App.tsx`:

```tsx
import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { RunListPage } from "./pages/RunListPage";
import { NewRunPage } from "./pages/NewRunPage";
import { StagePage } from "./pages/StagePage";
import { useRun } from "./api/queries";

function RunRedirect() {
  const { slug } = useParams<{ slug: string }>();
  const run = useRun(slug);

  if (run.isLoading) return <p>Loading run…</p>;
  if (run.isError || !run.data) return <p role="alert">Could not load run '{slug}'.</p>;

  const current = run.data.stages.find((row) => !run.data.approved_stages.includes(row.stage));
  const stage = current?.stage ?? run.data.stages[run.data.stages.length - 1]?.stage ?? "01";
  return <Navigate to={`/runs/${slug}/stages/${stage}`} replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<RunListPage />} />
      <Route path="/runs/new" element={<NewRunPage />} />
      <Route path="/runs/:slug" element={<RunRedirect />} />
      <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
    </Routes>
  );
}
```

- [ ] **Step 4: Run the full test suite to verify everything passes**

Run (from `_client/`): `npm test`
Expected: PASS — every test file in `_client/src/`.

- [ ] **Step 5: Commit**

```bash
git add _client/src/pages/StagePage.tsx _client/src/pages/StagePage.test.tsx _client/src/App.tsx _client/src/App.test.tsx
git commit -m "Add StagePage and wire final app routing

Completes the full stage loop: run list -> new run -> per-stage chat,
document, diff, approve/reject -- against the 01-design pipeline.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Manual verification (not automated, do once after Task 16)

1. From `_server/`: `python -m app.main` (starts the backend on `127.0.0.1:8000`; requires a real `ANTHROPIC_API_KEY` in the environment).
2. From `_client/`: `npm run dev` (starts Vite on `http://localhost:5173`).
3. Open the browser, click "New run", type a brief, click Start, and confirm the chat responds.
4. Once the model calls `create_run`, click "Check for created run" and confirm you land on `/runs/<slug>/stages/01`.
5. Continue the conversation until the model calls `mark_ready_for_review`; confirm the review banner appears, "View diff" shows the change, and "Approve" advances the stage rail.
6. Edit the document directly in the pane, click Save, and confirm the change persists on reload.
7. Start stage 2, then reject it back to stage 1 with a reason; confirm stage 1 unlocks for editing again and the loop-back appears in `worksheets/<slug>/RUN.md`.

This exercises the one thing the automated test suite can't: the real Anthropic model actually behaving like the fixtures assume.
