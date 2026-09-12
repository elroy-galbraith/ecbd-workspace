# Stage screen VS Code–style layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the stage screen from vertical-rail + bottom chat drawer into a VS Code–style layout: a horizontal stage rail, a collapsible file tree browsing the run's whole worksheet folder, and chat as a collapsible right-side panel.

**Architecture:** One new read-only backend endpoint (`GET /runs/{slug}/tree`) that walks a run's worksheet folder. One new frontend component (`FileTree`) that renders that tree and navigates to a file's owning stage on click. `StageRail` and `ChatDrawer` keep their existing logic and only gain new CSS (horizontal orientation; a `panel` layout variant) — no behavior changes to gating, approval, or chat/session handling.

**Tech Stack:** FastAPI + pytest (backend), React + TypeScript + Vite + TanStack Query + react-router-dom + vitest/@testing-library (frontend). No new dependencies.

**Spec:** [docs/superpowers/specs/2026-09-12-stages-ui-vscode-layout-design.md](../specs/2026-09-12-stages-ui-vscode-layout-design.md)

## Global Constraints

- No new npm or pip dependencies — build with the existing stack only.
- No drag-to-resize on any panel — collapse/expand only, at fixed widths (spec decision).
- The chat panel renders only when `run.data.mode === "design"` — never reserve layout space for it on other modes (spec decision).
- Reuse existing CSS custom properties from `_client/src/index.css` (`--bg-alt`, `--border-soft`, `--muted`, `--fg`, `--faint`, `--accent`, `--accent-wash`, `--font-mono`, `--font-sans`) — no new design tokens.
- `.chat-drawer`'s existing base styling (used today by `NewRunPage`) must not change — the new right-panel look is an additive `chat-drawer--panel` modifier class, applied only where `StagePage` opts in.
- A file tree leaf that doesn't belong to any stage (nothing in `run.data.stages[].file` matches it) renders inert, not as a broken link — same gap `DocumentPane` already has for directory-shaped stage outputs (no viewer route exists for arbitrary files yet).

---

### Task 1: Backend — `GET /runs/{slug}/tree`

**Files:**
- Modify: `_server/app/main.py` (add `_build_tree` helper near `_resolve_run_file`, add the route near `get_file`/`put_file`)
- Test: `_server/tests/test_api.py`

**Interfaces:**
- Produces: `GET /runs/{slug}/tree` → `{"tree": TreeNode[]}` where `TreeNode = {"name": str, "path": str, "is_dir": bool, "children": TreeNode[] | None}`. `path` is POSIX-style, relative to the run root, and is exactly what `GET`/`PUT /runs/{slug}/files/{path}` already accept.

- [ ] **Step 1: Write the failing tests**

Add to `_server/tests/test_api.py` (near the other `get_file`/`put_file` tests):

```python
def test_get_tree_lists_nested_files(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    (run_root / "08_build").mkdir(parents=True)
    (run_root / "01_intended-use.md").write_text("hello", encoding="utf-8")
    (run_root / "08_build" / "eval.jsonl").write_text("{}", encoding="utf-8")

    response = api.get("/runs/design-my-eval/tree")
    assert response.status_code == 200
    assert response.json() == {
        "tree": [
            {
                "name": "08_build",
                "path": "08_build",
                "is_dir": True,
                "children": [
                    {"name": "eval.jsonl", "path": "08_build/eval.jsonl", "is_dir": False, "children": None},
                ],
            },
            {"name": "01_intended-use.md", "path": "01_intended-use.md", "is_dir": False, "children": None},
        ]
    }


def test_get_tree_skips_dotfiles_and_sessions_dir(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    run_root = tmp_repo / "worksheets" / "design-my-eval"
    (run_root / ".sessions").mkdir(parents=True)
    (run_root / ".sessions" / "01.jsonl").write_text("{}", encoding="utf-8")
    (run_root / ".hidden").write_text("secret", encoding="utf-8")
    (run_root / "RUN.md").write_text("# run", encoding="utf-8")

    response = api.get("/runs/design-my-eval/tree")
    assert response.status_code == 200
    assert response.json() == {"tree": [{"name": "RUN.md", "path": "RUN.md", "is_dir": False, "children": None}]}


def test_get_tree_empty_run(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    (tmp_repo / "worksheets" / "design-my-eval").mkdir(parents=True)

    response = api.get("/runs/design-my-eval/tree")
    assert response.status_code == 200
    assert response.json() == {"tree": []}


def test_get_tree_404_for_missing_run(tmp_repo: Path):
    app = create_app(model_client=FakeModelClient([]), repo_root=tmp_repo)
    api = TestClient(app)
    response = api.get("/runs/design-nonexistent/tree")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd _server && python -m pytest tests/test_api.py -k test_get_tree -v`
Expected: FAIL — `404 Not Found` / `AssertionError` since the route doesn't exist yet (FastAPI returns 404 for any unknown route).

- [ ] **Step 3: Add `_build_tree` and the route**

In `_server/app/main.py`, add next to `_resolve_run_file` (around line 47):

```python
def _build_tree(directory: Path, root: Path) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for child in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if child.name.startswith("."):  # covers .sessions/ and any other dotfile
            continue
        rel_path = child.relative_to(root).as_posix()
        if child.is_dir():
            nodes.append(
                {"name": child.name, "path": rel_path, "is_dir": True, "children": _build_tree(child, root)}
            )
        else:
            nodes.append({"name": child.name, "path": rel_path, "is_dir": False, "children": None})
    return nodes
```

Then add the route in `create_app`, directly after `put_file` (around line 271, before `return app`):

```python
    @app.get("/runs/{slug}/tree")
    def get_tree(slug: str) -> dict[str, Any]:
        run_root = repo_root / "worksheets" / slug
        if not run_root.exists():
            raise HTTPException(404, f"run '{slug}' does not exist")
        return {"tree": _build_tree(run_root, run_root)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _server && python -m pytest tests/test_api.py -k test_get_tree -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Run the full backend test suite**

Run: `cd _server && python -m pytest -v`
Expected: PASS (no regressions)

- [ ] **Step 6: Commit**

```bash
git add _server/app/main.py _server/tests/test_api.py
git commit -m "feat(backend): add GET /runs/:slug/tree for browsing a run's files"
```

---

### Task 2: Frontend — `RunTreeNode` type and `useRunTree` query

**Files:**
- Modify: `_client/src/api/types.ts`
- Modify: `_client/src/api/queries.ts`
- Test: `_client/src/api/queries.test.tsx`

**Interfaces:**
- Produces: `RunTreeNode = { name: string; path: string; is_dir: boolean; children: RunTreeNode[] | null }`, `RunTree = { tree: RunTreeNode[] }`, `useRunTree(slug: string | undefined) => UseQueryResult<RunTree>` (query key `["tree", slug]`).

- [ ] **Step 1: Add the types**

In `_client/src/api/types.ts`, add after `RunDetail`:

```ts
export interface RunTreeNode {
  name: string;
  path: string;
  is_dir: boolean;
  children: RunTreeNode[] | null;
}

export interface RunTree {
  tree: RunTreeNode[];
}
```

- [ ] **Step 2: Write the failing test**

Add to `_client/src/api/queries.test.tsx`:

```tsx
import { useRunTree } from "./queries";

describe("useRunTree", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches a run's file tree from /runs/:slug/tree", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        tree: [{ name: "RUN.md", path: "RUN.md", is_dir: false, children: null }],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useRunTree("design-my-eval"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({
      tree: [{ name: "RUN.md", path: "RUN.md", is_dir: false, children: null }],
    });
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/runs/design-my-eval/tree"), expect.anything());
  });
});
```

(Add the `useRunTree` import to the existing `import { useRuns } from "./queries";` line rather than duplicating it, and add a second `describe` block below the existing one — `wrapper`, `waitFor`, `renderHook` etc. are already imported at the top of the file.)

- [ ] **Step 3: Run test to verify it fails**

Run: `cd _client && npx vitest run src/api/queries.test.tsx`
Expected: FAIL — `useRunTree is not a function` / `TypeError`

- [ ] **Step 4: Add `useRunTree`**

In `_client/src/api/queries.ts`, add after `useRunFile`:

```ts
export function useRunTree(slug: string | undefined) {
  return useQuery({
    queryKey: ["tree", slug],
    queryFn: () => api.get<RunTree>(`/runs/${slug}/tree`),
    enabled: slug !== undefined,
  });
}
```

Add `RunTree` to the existing `import type { ... } from "./types"` line.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd _client && npx vitest run src/api/queries.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add _client/src/api/types.ts _client/src/api/queries.ts _client/src/api/queries.test.tsx
git commit -m "feat(frontend): add useRunTree query for a run's file tree"
```

---

### Task 3: Frontend — panel collapse persistence in `sessionStorage.ts`

**Files:**
- Modify: `_client/src/lib/sessionStorage.ts`
- Test: `_client/src/lib/sessionStorage.test.ts`

**Interfaces:**
- Produces: `type PanelKey = "file-tree" | "chat"`, `loadPanelCollapsed(runKey: string, panel: PanelKey): boolean | null` (null = nothing stored yet — caller decides the default), `storePanelCollapsed(runKey: string, panel: PanelKey, collapsed: boolean): void`.

- [ ] **Step 1: Write the failing tests**

Add to `_client/src/lib/sessionStorage.test.ts`:

```ts
import { clearSessionId, loadPanelCollapsed, loadSessionId, storePanelCollapsed, storeSessionId } from "./sessionStorage";

describe("panel collapse helpers", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns null when nothing is stored", () => {
    expect(loadPanelCollapsed("design-my-eval", "chat")).toBeNull();
  });

  it("round-trips a stored collapse flag", () => {
    storePanelCollapsed("design-my-eval", "chat", true);
    expect(loadPanelCollapsed("design-my-eval", "chat")).toBe(true);

    storePanelCollapsed("design-my-eval", "chat", false);
    expect(loadPanelCollapsed("design-my-eval", "chat")).toBe(false);
  });

  it("keeps file-tree and chat collapse state independent", () => {
    storePanelCollapsed("design-my-eval", "file-tree", true);
    storePanelCollapsed("design-my-eval", "chat", false);

    expect(loadPanelCollapsed("design-my-eval", "file-tree")).toBe(true);
    expect(loadPanelCollapsed("design-my-eval", "chat")).toBe(false);
  });

  it("does not throw when localStorage access fails", () => {
    const spy = vi.spyOn(window.localStorage.__proto__, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(() => storePanelCollapsed("design-my-eval", "chat", true)).not.toThrow();
    spy.mockRestore();
  });
});
```

(Update the top-of-file import to pull in `loadPanelCollapsed`/`storePanelCollapsed` alongside the existing named imports.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd _client && npx vitest run src/lib/sessionStorage.test.ts`
Expected: FAIL — `loadPanelCollapsed is not a function`

- [ ] **Step 3: Implement the helpers**

In `_client/src/lib/sessionStorage.ts`, add below the existing session-id helpers:

```ts
export type PanelKey = "file-tree" | "chat";

function collapseKey(runKey: string, panel: PanelKey): string {
  return `ecbd-collapse:${panel}:${runKey}`;
}

export function loadPanelCollapsed(runKey: string, panel: PanelKey): boolean | null {
  try {
    const raw = window.localStorage.getItem(collapseKey(runKey, panel));
    return raw === null ? null : raw === "true";
  } catch {
    return null;
  }
}

export function storePanelCollapsed(runKey: string, panel: PanelKey, collapsed: boolean): void {
  try {
    window.localStorage.setItem(collapseKey(runKey, panel), String(collapsed));
  } catch {
    // localStorage unavailable -- the collapse state just won't survive a refresh
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _client && npx vitest run src/lib/sessionStorage.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _client/src/lib/sessionStorage.ts _client/src/lib/sessionStorage.test.ts
git commit -m "feat(frontend): persist file-tree/chat panel collapse state per run"
```

---

### Task 4: Frontend — `FileTree` component

**Files:**
- Modify: `_client/src/components/icons.tsx` (add `IconFile`)
- Create: `_client/src/components/FileTree.tsx`
- Modify: `_client/src/index.css` (append `.file-tree` styles)
- Test: `_client/src/components/FileTree.test.tsx`

**Interfaces:**
- Consumes: `useRunTree(slug)` (Task 2), `loadPanelCollapsed`/`storePanelCollapsed` (Task 3), `isStageUnlocked(stages, approvedStages, stage): boolean` (already exported from `StageRail.tsx`), `StageTableRow`/`RunTreeNode` (`../api/types`).
- Produces: `FileTree({ slug, stages, approvedStages, activeStage, gated }): JSX.Element`, and an exported helper `findOwningStage(stages: StageTableRow[], path: string): string | undefined` (used by `FileTree` itself; Task 6 does not need to call it directly since navigation stays link-based).

- [ ] **Step 1: Add `IconFile`**

In `_client/src/components/icons.tsx`, add after `IconFolder`:

```tsx
export function IconFile(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path
        d="M6.5 3.5h5l3 3v10a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-12a1 1 0 0 1 1-1Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path d="M11.5 3.5V6.5a1 1 0 0 0 1 1H15.5" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}
```

- [ ] **Step 2: Write the failing tests**

Create `_client/src/components/FileTree.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { FileTree, findOwningStage } from "./FileTree";
import type { RunTreeNode } from "../api/types";
import type { StageTableRow } from "../api/types";

const mockUseRunTree = vi.fn();
vi.mock("../api/queries", () => ({
  useRunTree: (...args: unknown[]) => mockUseRunTree(...args),
}));

const mockLoadPanelCollapsed = vi.fn();
const mockStorePanelCollapsed = vi.fn();
vi.mock("../lib/sessionStorage", () => ({
  loadPanelCollapsed: (...args: unknown[]) => mockLoadPanelCollapsed(...args),
  storePanelCollapsed: (...args: unknown[]) => mockStorePanelCollapsed(...args),
}));

const stages: StageTableRow[] = [
  { file: "01_intended-use.md", stage: "01", questions: "Q1-2", done: true },
  { file: "02_capability.md", stage: "02", questions: "Q3-5", done: false },
  { file: "08_build/", stage: "08", questions: "Q9", done: false },
];

const tree: RunTreeNode[] = [
  { name: "01_intended-use.md", path: "01_intended-use.md", is_dir: false, children: null },
  { name: "02_capability.md", path: "02_capability.md", is_dir: false, children: null },
  {
    name: "08_build",
    path: "08_build",
    is_dir: true,
    children: [{ name: "eval.jsonl", path: "08_build/eval.jsonl", is_dir: false, children: null }],
  },
  { name: "RUN.md", path: "RUN.md", is_dir: false, children: null },
];

beforeEach(() => {
  vi.clearAllMocks();
  mockLoadPanelCollapsed.mockReturnValue(null);
  mockUseRunTree.mockReturnValue({ data: { tree }, isLoading: false, isError: false });
});

describe("findOwningStage", () => {
  it("matches an exact file path", () => {
    expect(findOwningStage(stages, "01_intended-use.md")).toBe("01");
  });

  it("matches a file nested under a directory-shaped stage", () => {
    expect(findOwningStage(stages, "08_build/eval.jsonl")).toBe("08");
  });

  it("returns undefined for a path with no owning stage", () => {
    expect(findOwningStage(stages, "RUN.md")).toBeUndefined();
  });
});

describe("FileTree", () => {
  it("renders files as links to their owning stage", () => {
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={["01"]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    const stage2File = screen.getByRole("link", { name: /02_capability\.md/ });
    expect(stage2File).toHaveAttribute("href", "/runs/design-my-eval/stages/02");
  });

  it("renders a file whose stage is locked as disabled, not a link", () => {
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={[]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    const locked = screen.getByText("02_capability.md");
    expect(locked).toHaveAttribute("aria-disabled", "true");
    expect(screen.queryByRole("link", { name: /02_capability\.md/ })).not.toBeInTheDocument();
  });

  it("renders a file with no owning stage as inert", () => {
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={["01"]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    const inert = screen.getByText("RUN.md");
    expect(inert).toHaveAttribute("aria-disabled", "true");
    expect(screen.queryByRole("link", { name: /RUN\.md/ })).not.toBeInTheDocument();
  });

  it("renders a nested file under an expanded directory", () => {
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={["01", "02"]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /eval\.jsonl/ })).toHaveAttribute(
      "href",
      "/runs/design-my-eval/stages/08",
    );
  });

  it("toggles collapsed state and persists it", async () => {
    const { default: userEvent } = await import("@testing-library/user-event");
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={["01"]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    await userEvent.setup().click(screen.getByRole("button", { name: /collapse files/i }));
    expect(mockStorePanelCollapsed).toHaveBeenCalledWith("design-my-eval", "file-tree", true);
    expect(screen.getByRole("button", { name: /expand files/i })).toBeInTheDocument();
  });

  it("ungated (audit/measure) runs never render a locked file", () => {
    render(
      <MemoryRouter>
        <FileTree slug="audit-my-eval" stages={stages} approvedStages={[]} activeStage="01" gated={false} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /02_capability\.md/ })).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd _client && npx vitest run src/components/FileTree.test.tsx`
Expected: FAIL — cannot find module `./FileTree`

- [ ] **Step 4: Implement `FileTree.tsx`**

Create `_client/src/components/FileTree.tsx`:

```tsx
import { useState } from "react";
import { Link } from "react-router-dom";
import { useRunTree } from "../api/queries";
import { loadPanelCollapsed, storePanelCollapsed } from "../lib/sessionStorage";
import type { RunTreeNode, StageTableRow } from "../api/types";
import { isStageUnlocked } from "./StageRail";
import { IconFile, IconFolder, IconLock } from "./icons";

interface FileTreeProps {
  slug: string;
  stages: StageTableRow[];
  approvedStages: string[];
  activeStage: string;
  gated: boolean;
}

export function findOwningStage(stages: StageTableRow[], path: string): string | undefined {
  let best: StageTableRow | undefined;
  for (const row of stages) {
    const rowPath = row.file.replace(/\/$/, "");
    if (path !== rowPath && !path.startsWith(`${rowPath}/`)) continue;
    if (!best || rowPath.length > best.file.replace(/\/$/, "").length) {
      best = row;
    }
  }
  return best?.stage;
}

export function FileTree({ slug, stages, approvedStages, activeStage, gated }: FileTreeProps) {
  const tree = useRunTree(slug);
  const [collapsed, setCollapsed] = useState(() => loadPanelCollapsed(slug, "file-tree") ?? false);

  function toggle() {
    setCollapsed((current) => {
      const next = !current;
      storePanelCollapsed(slug, "file-tree", next);
      return next;
    });
  }

  return (
    <nav aria-label="Run files" className={`file-tree${collapsed ? " file-tree--collapsed" : ""}`}>
      <button type="button" className="file-tree__toggle" onClick={toggle}>
        <IconFolder width={14} height={14} />
        {collapsed ? "Expand files" : "Collapse files"}
      </button>
      {!collapsed && (
        <div className="file-tree__nodes">
          {tree.isLoading && <p className="file-tree__notice">Loading files…</p>}
          {tree.isError && <p role="alert">Could not load files.</p>}
          {tree.data?.tree.map((node) => (
            <TreeNode
              key={node.path}
              node={node}
              slug={slug}
              stages={stages}
              approvedStages={approvedStages}
              activeStage={activeStage}
              gated={gated}
            />
          ))}
        </div>
      )}
    </nav>
  );
}

interface TreeNodeProps extends FileTreeProps {
  node: RunTreeNode;
}

function TreeNode({ node, slug, stages, approvedStages, activeStage, gated }: TreeNodeProps) {
  if (node.is_dir) {
    return (
      <details className="file-tree__dir" open>
        <summary>
          <IconFolder width={13} height={13} />
          {node.name}
        </summary>
        <div className="file-tree__children">
          {(node.children ?? []).map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              slug={slug}
              stages={stages}
              approvedStages={approvedStages}
              activeStage={activeStage}
              gated={gated}
            />
          ))}
        </div>
      </details>
    );
  }

  const owningStage = findOwningStage(stages, node.path);
  if (owningStage === undefined) {
    return (
      <span className="file-tree__file file-tree__file--inert" aria-disabled="true">
        <IconFile width={13} height={13} />
        {node.name}
      </span>
    );
  }

  const unlocked = gated ? isStageUnlocked(stages, approvedStages, owningStage) : true;
  if (!unlocked) {
    return (
      <span className="file-tree__file file-tree__file--locked" aria-disabled="true">
        <IconLock width={12} height={12} />
        {node.name}
      </span>
    );
  }

  return (
    <Link
      to={`/runs/${slug}/stages/${owningStage}`}
      className={`file-tree__file${owningStage === activeStage ? " file-tree__file--active" : ""}`}
    >
      <IconFile width={13} height={13} />
      {node.name}
    </Link>
  );
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd _client && npx vitest run src/components/FileTree.test.tsx`
Expected: PASS

- [ ] **Step 6: Add `.file-tree` CSS**

Append to `_client/src/index.css` (near the "Stage rail" section):

```css
/* File tree */
.file-tree {
  width: 240px;
  flex-shrink: 0;
  padding: 16px 12px;
  border-right: 1px solid var(--border-soft);
  background: var(--bg-alt);
  overflow-y: auto;
  font-size: 13px;
}
.file-tree--collapsed {
  width: auto;
  padding: 16px 8px;
}
.file-tree__toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: var(--muted);
  font: 500 12.5px/1 var(--font-sans);
  cursor: pointer;
  padding: 4px 0;
  margin-bottom: 8px;
  white-space: nowrap;
}
.file-tree__toggle:hover {
  color: var(--fg);
}
.file-tree__dir > summary {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: var(--muted);
  list-style: none;
}
.file-tree__dir > summary::-webkit-details-marker {
  display: none;
}
.file-tree__dir > summary:hover {
  color: var(--fg);
}
.file-tree__children {
  margin-left: 14px;
  padding-left: 8px;
  border-left: 1px solid var(--border-soft);
}
.file-tree__file {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border-radius: 4px;
  text-decoration: none;
  color: var(--fg);
  font: 400 13px/1.3 var(--font-mono);
}
.file-tree__file:hover {
  background: var(--surface-2);
}
.file-tree__file--active {
  background: var(--accent-wash);
  color: var(--accent);
}
.file-tree__file--locked,
.file-tree__file--inert {
  color: var(--faint);
  cursor: default;
}
```

- [ ] **Step 7: Commit**

```bash
git add _client/src/components/icons.tsx _client/src/components/FileTree.tsx _client/src/components/FileTree.test.tsx _client/src/index.css
git commit -m "feat(frontend): add FileTree component for browsing a run's worksheet folder"
```

---

### Task 5: Frontend — `ChatDrawer` panel variant and collapse persistence

**Files:**
- Modify: `_client/src/components/ChatDrawer.tsx`
- Modify: `_client/src/index.css` (append `.chat-drawer--panel` styles)
- Test: `_client/src/components/ChatDrawer.test.tsx`

**Interfaces:**
- Consumes: `loadPanelCollapsed`/`storePanelCollapsed` (Task 3).
- Produces: `ChatDrawer` gains an optional `variant?: "drawer" | "panel"` prop (default `"drawer"`, preserving today's `NewRunPage` look unchanged). Root element className becomes `chat-drawer chat-drawer--{variant}[ chat-drawer--collapsed]`.

- [ ] **Step 1: Update the test's `sessionStorage` mock and add new tests**

In `_client/src/components/ChatDrawer.test.tsx`, replace the existing `vi.mock("../lib/sessionStorage", ...)` block with:

```tsx
const mockLoadSessionId = vi.fn();
const mockStoreSessionId = vi.fn();
const mockClearSessionId = vi.fn();
const mockLoadPanelCollapsed = vi.fn();
const mockStorePanelCollapsed = vi.fn();
vi.mock("../lib/sessionStorage", () => ({
  loadSessionId: (...args: unknown[]) => mockLoadSessionId(...args),
  storeSessionId: (...args: unknown[]) => mockStoreSessionId(...args),
  clearSessionId: (...args: unknown[]) => mockClearSessionId(...args),
  loadPanelCollapsed: (...args: unknown[]) => mockLoadPanelCollapsed(...args),
  storePanelCollapsed: (...args: unknown[]) => mockStorePanelCollapsed(...args),
}));
```

Add `mockLoadPanelCollapsed.mockReturnValue(null);` to the existing `beforeEach`'s default mocks.

Add two new tests inside `describe("ChatDrawer", ...)`:

```tsx
  it("defaults to collapsed when nothing is stored (matching today's behavior), and persists an expand", async () => {
    mockLoadSessionId.mockReturnValue("sess-1");
    mockUseSession.mockReturnValue({
      data: { transcript: [], ready_for_review: false },
      isError: false,
      error: null,
    });

    render(<ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} variant="panel" />);

    expect(screen.getByRole("button", { name: /expand chat/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /expand chat/i }));
    expect(mockStorePanelCollapsed).toHaveBeenCalledWith("design-my-eval", "chat", false);
  });

  it("restores a previously-expanded panel from storage", () => {
    mockLoadSessionId.mockReturnValue("sess-1");
    mockLoadPanelCollapsed.mockReturnValue(false);
    mockUseSession.mockReturnValue({
      data: { transcript: [], ready_for_review: false },
      isError: false,
      error: null,
    });

    render(<ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} variant="panel" />);

    expect(screen.getByRole("button", { name: /collapse chat/i })).toBeInTheDocument();
  });

  it("applies the panel variant class when requested, and the drawer variant by default", () => {
    mockLoadSessionId.mockReturnValue(null);
    const { container: panelContainer } = render(
      <ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} variant="panel" />,
    );
    expect(panelContainer.querySelector(".chat-drawer--panel")).toBeInTheDocument();

    const { container: drawerContainer } = render(
      <ChatDrawer runKey="new" stage="01" startSession={vi.fn()} />,
    );
    expect(drawerContainer.querySelector(".chat-drawer--drawer")).toBeInTheDocument();
  });
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `cd _client && npx vitest run src/components/ChatDrawer.test.tsx`
Expected: FAIL — no `variant` prop yet, panel defaults to collapsed (`true`), no `chat-drawer--{variant}` class

- [ ] **Step 3: Implement the variant prop and collapse persistence**

In `_client/src/components/ChatDrawer.tsx`:

Change the imports:

```tsx
import { clearSessionId, loadPanelCollapsed, loadSessionId, storePanelCollapsed, storeSessionId } from "../lib/sessionStorage";
```

Change the props interface and function signature:

```tsx
interface ChatDrawerProps {
  runKey: string;
  stage: string;
  startSession: (brief: string) => Promise<{ session_id: string }>;
  onSessionId?: (sessionId: string) => void;
  variant?: "drawer" | "panel";
}

export function ChatDrawer({ runKey, stage, startSession, onSessionId, variant = "drawer" }: ChatDrawerProps) {
  const [sessionId, setSessionId] = useState<string | null>(() => loadSessionId(runKey, stage));
  const [collapsed, setCollapsed] = useState(() => loadPanelCollapsed(runKey, "chat") ?? true);
```

Add a toggle helper next to `handleForget` and use it from the toggle button:

```tsx
  function toggleCollapsed() {
    setCollapsed((current) => {
      const next = !current;
      storePanelCollapsed(runKey, "chat", next);
      return next;
    });
  }
```

In `handleStart`, replace `setCollapsed(false);` with:

```tsx
      setCollapsed(false);
      storePanelCollapsed(runKey, "chat", false);
```

Update both root-element `className`s and the toggle button's `onClick`:

```tsx
  if (sessionId === null || sessionGone) {
    return (
      <div className={`chat-drawer chat-drawer--${variant} chat-drawer--empty`}>
        {/* ...unchanged content... */}
      </div>
    );
  }

  return (
    <div className={`chat-drawer chat-drawer--${variant}${collapsed ? " chat-drawer--collapsed" : ""}`}>
      <button className="chat-drawer__toggle" onClick={toggleCollapsed}>
        <IconChat width={15} height={15} />
        {collapsed ? "Expand chat" : "Collapse chat"}
      </button>
      {/* ...unchanged content... */}
    </div>
  );
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd _client && npx vitest run src/components/ChatDrawer.test.tsx`
Expected: PASS

- [ ] **Step 5: Add `.chat-drawer--panel` CSS**

Append to `_client/src/index.css` (near the existing "chat-drawer" rules, after `.chat-drawer--empty`'s block):

```css
.chat-drawer--panel {
  border-top: none;
  border-left: 1px solid var(--border-soft);
  max-height: none;
  height: 100%;
  width: 320px;
  flex-shrink: 0;
}
.chat-drawer--panel.chat-drawer--collapsed {
  width: auto;
  overflow: hidden;
}
.chat-drawer--panel.chat-drawer--collapsed .chat-drawer__toggle {
  margin: 12px;
}
```

`.chat-drawer--drawer` gets no CSS rule at all — it's a marker class only (asserted by Step 1's third new test), needed so the panel/drawer distinction exists in the DOM without touching the bare `.chat-drawer` selector's existing rules. Since `.chat-drawer--panel`'s properties (`border-top: none`, `max-height: none`, etc.) only apply where that class is present, the pre-existing bare `.chat-drawer` rule stays exactly as written and `NewRunPage`'s current look (which renders `chat-drawer chat-drawer--drawer chat-drawer--empty`, picking up no new styling) is unaffected.

- [ ] **Step 6: Run the full frontend test suite**

Run: `cd _client && npx vitest run`
Expected: PASS (no regressions in `NewRunPage.test.tsx` or elsewhere)

- [ ] **Step 7: Commit**

```bash
git add _client/src/components/ChatDrawer.tsx _client/src/components/ChatDrawer.test.tsx _client/src/index.css
git commit -m "feat(frontend): add a right-panel ChatDrawer variant with persisted collapse state"
```

---

### Task 6: Frontend — horizontal `StageRail`

**Files:**
- Modify: `_client/src/index.css` (rewrite the "Stage rail" section's property values only — no selector changes)

**Interfaces:**
- Consumes/produces: none — `StageRail.tsx`'s props, exports (`isStageUnlocked`, `stageName`), and JSX structure are unchanged. This is a pure CSS orientation change on the existing `.stage-rail`, `.stage-rail__item`, `.stage-rail__marker`, `.stage-rail__dot`, `.stage-rail__connector` selectors.

- [ ] **Step 1: Confirm the existing tests still describe the right behavior**

Run: `cd _client && npx vitest run src/components/StageRail.test.tsx`
Expected: PASS (these tests assert link/lock behavior via role and `href`/`aria-disabled`, not layout — they must stay green through this task since nothing about StageRail's DOM structure or props changes)

- [ ] **Step 2: Replace the "Stage rail" CSS block**

In `_client/src/index.css`, replace the block from `.stage-rail {` through the end of `.stage-rail__connector { ... }` with:

```css
/* Stage rail */
.stage-rail {
  width: 100%;
  flex-shrink: 0;
  padding: 14px 24px;
  border-right: none;
  border-bottom: 1px solid var(--border-soft);
  background: var(--bg-alt);
  overflow-x: auto;
  overflow-y: hidden;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;
}
.stage-rail__item {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: inherit;
  font-size: 13px;
  white-space: nowrap;
  flex-shrink: 0;
}
.stage-rail__marker {
  display: flex;
  flex-direction: row;
  align-items: center;
}
.stage-rail__dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--accent-ink);
}
.stage-rail__connector {
  height: 2px;
  width: 28px;
  min-width: 18px;
  flex: 0 1 auto;
  margin: 0 8px;
  background: var(--border-soft);
}
```

Every rule below this block that targets `.stage-rail__item--*`/`.stage-rail__dot`/`.stage-rail__connector` state modifiers (approved/active/upcoming/locked colors) stays exactly as-is — only the base geometry rules above change.

- [ ] **Step 3: Run tests to verify no regressions**

Run: `cd _client && npx vitest run src/components/StageRail.test.tsx`
Expected: PASS

- [ ] **Step 4: Manual visual check**

This step has no automated assertion — it's a pure CSS change with no jsdom-visible effect. Start the dev server and confirm visually once Task 7 wires `StageRail` into its new position (deferred to Task 7's Step 7, since `StageRail` isn't reachable in its new full-width slot until `StagePage` moves it there).

- [ ] **Step 5: Commit**

```bash
git add _client/src/index.css
git commit -m "style(frontend): reorient the stage rail from vertical to horizontal"
```

---

### Task 7: Frontend — wire it all into `StagePage`

**Files:**
- Modify: `_client/src/pages/StagePage.tsx`
- Test: `_client/src/pages/StagePage.test.tsx`

No `index.css` change is needed here: `.stage-page__body`'s existing `display: flex; flex: 1; min-height: 0;` already accommodates a three-child row (`FileTree`, `main.stage-page__document`, `ChatDrawer`) exactly as it accommodated the previous two-child row — the fixed-width/flex-shrink behavior for the new children comes from `.file-tree` (Task 4) and `.chat-drawer--panel` (Task 5)'s own CSS.

**Interfaces:**
- Consumes: `FileTree` (Task 4), `ChatDrawer`'s `variant` prop (Task 5), horizontal `StageRail` CSS (Task 6), `useRunTree` (Task 2, via `FileTree`).

- [ ] **Step 1: Update `StagePage.test.tsx`'s mocks**

In `_client/src/pages/StagePage.test.tsx`, add `useRunTree` to the existing `vi.mock("../api/queries", ...)` factory:

```tsx
vi.mock("../api/queries", () => ({
  useRun: (...args: unknown[]) => mockUseRun(...args),
  useSession: (...args: unknown[]) => mockUseSession(...args),
  useStageDiff: () => ({ data: undefined }),
  useRuns: () => ({ data: [] }),
  useRunFile: () => ({ data: undefined, isLoading: true, isError: false }),
  useRunTree: () => ({ data: { tree: [] }, isLoading: false, isError: false }),
}));
```

- [ ] **Step 2: Add a failing test for the new layout piece**

Add inside `describe("StagePage", ...)`:

```tsx
  it("renders the file tree alongside the stage rail and document", () => {
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("navigation", { name: /stage progress/i })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: /run files/i })).toBeInTheDocument();
  });
```

- [ ] **Step 3: Run tests to verify the new one fails**

Run: `cd _client && npx vitest run src/pages/StagePage.test.tsx`
Expected: FAIL — no element with accessible name "Run files" yet

- [ ] **Step 4: Restructure `StagePage.tsx`**

Add the import:

```tsx
import { FileTree } from "../components/FileTree";
```

Change the returned JSX so `StageRail` moves out of `.stage-page__body` into its own full-width row, and `FileTree` + a `variant="panel"` `ChatDrawer` flank the document pane:

```tsx
  return (
    <div className="stage-page">
      <header className="stage-page__header">
        <Link to="/" className="brand">
          <span className="brand__mark" aria-hidden="true" />
          ECBD
        </Link>
        <div className="stage-page__divider" aria-hidden="true" />
        <div className="crumb">
          <RunSwitcher currentSlug={slug} />
          <span className="crumb__sep" aria-hidden="true">/</span>
          <span className="crumb__stage mono">stage {stage}</span>
        </div>
        <Link to="/runs/new" className="btn btn--ghost stage-page__new-run">
          <IconPlus width={14} height={14} />
          New run
        </Link>
      </header>
      <StageRail
        slug={slug}
        stages={run.data.stages}
        approvedStages={run.data.approved_stages}
        activeStage={stage}
        gated={isDesign}
      />
      <div className="stage-page__body">
        <FileTree
          slug={slug}
          stages={run.data.stages}
          approvedStages={run.data.approved_stages}
          activeStage={stage}
          gated={isDesign}
        />
        <main className="stage-page__document">
          {isDesign && readyForReview && (
            <ReviewBanner
              onViewDiff={() => setShowDiff(true)}
              onApprove={() => approve.mutate()}
              onReject={() => setShowReject(true)}
              approving={approve.isPending}
            />
          )}
          {isDesign && showDiff && diff.data && <DiffView diff={diff.data.diff} />}
          {currentRow && <DocumentPane slug={slug} file={currentRow.file} />}
          {isDesign && showReject && (
            <RejectDialog
              approvedStages={run.data.approved_stages}
              currentStage={stage}
              onSubmit={(input) =>
                reject.mutate(input, {
                  onSuccess: () => {
                    setShowReject(false);
                    const targetIndex = stageOrder.indexOf(input.target_stage);
                    const currentIndex = stageOrder.indexOf(stage);
                    if (targetIndex !== -1 && currentIndex !== -1) {
                      for (const s of stageOrder.slice(targetIndex, currentIndex + 1)) {
                        clearSessionId(slug, s);
                      }
                    }
                  },
                })
              }
              onCancel={() => setShowReject(false)}
            />
          )}
        </main>
        {isDesign && (
          <ChatDrawer
            variant="panel"
            runKey={slug}
            stage={stage}
            startSession={(brief) => startStage.mutateAsync(brief)}
            onSessionId={setSessionId}
          />
        )}
      </div>
    </div>
  );
```

(Everything inside `<main className="stage-page__document">` is unchanged from today — only its position, now inside a three-child `.stage-page__body` row instead of a two-child one, and `StageRail`'s new position directly under the header, changed.)

- [ ] **Step 5: Run tests to verify everything passes**

Run: `cd _client && npx vitest run src/pages/StagePage.test.tsx`
Expected: PASS (all existing tests plus the new one)

- [ ] **Step 6: Run the full frontend test suite**

Run: `cd _client && npx vitest run`
Expected: PASS (no regressions anywhere — `NewRunPage.test.tsx`, `App.test.tsx`, `App.remount.test.tsx` included)

- [ ] **Step 7: Manual visual verification**

Run: `cd _client && npm run dev`, open the app, start or open a design run, and confirm:
- The stage rail runs horizontally under the header and scrolls if narrow.
- The file tree appears on the left, browsing the whole run folder; clicking a file navigates to its owning stage.
- A locked stage's files show as disabled (lock icon), matching the rail's own locked items.
- The chat panel sits on the right, collapses/expands, and the collapsed state survives a page reload.
- An audit or measure run (no chat panel) still shows the file tree and horizontal rail correctly, with no reserved chat space.

- [ ] **Step 8: Commit**

```bash
git add _client/src/pages/StagePage.tsx _client/src/pages/StagePage.test.tsx
git commit -m "feat(frontend): assemble the VS Code-style stage screen layout"
```
