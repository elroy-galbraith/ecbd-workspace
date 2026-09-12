---
date: 2026-09-12
status: approved, not yet implemented
decision: Rework the stage screen into a VS Code–style layout — horizontal stage rail, collapsible run-wide file tree, chat as a right-side panel instead of a bottom drawer
---

# Stage screen: VS Code–style layout

## Context

`docs/superpowers/specs/2026-09-09-orchestrator-frontend-design.md` shipped the current stage screen: a vertical stage rail on the left, the current stage's single document filling the rest, and chat as a bottom drawer. That layout was chosen because "the document is what you spend the most time reading and a drawer keeps it full-width."

Two things have since made that layout feel cramped: the design pipeline has eight stages, which crowds a vertical rail meant to also hold the run switcher above it; and there is no way to look at any file other than the one the current stage happens to point at ([`DocumentPane`](../../../_client/src/components/DocumentPane.tsx) only ever renders `currentRow.file`, and no endpoint lists a run's other files). This record moves to a layout familiar from VS Code — persistent chrome for navigation top and side, a focused center pane, chat as a dockable side panel — and adds the one piece of new backend surface that layout requires: a way to list a run's files.

This is frontend-only except for one new read endpoint. No existing route, stage contract, or approval/gating behavior changes.

## Decision

- **Stage rail moves from a vertical left column to a horizontal strip** between the header and the body, spanning the full width. Same underlying state machine (`approved` / `active` / `upcoming` / `locked`, from [`StageRail.tsx`](../../../_client/src/components/StageRail.tsx)'s `isStageUnlocked`) — only the CSS axis and marker/connector geometry change from vertical to horizontal.
- **A new collapsible file tree sits on the left of the document pane**, browsing the *entire* run's worksheet folder (`worksheets/{slug}/`), not just the current stage's file — so a person can jump to any stage's output regardless of which stage they're currently on.
- **Chat moves from a full-width bottom drawer to a collapsible right-side panel**, present only for `mode === "design"` runs, matching today's `isDesign` gate in [`StagePage.tsx`](../../../_client/src/pages/StagePage.tsx) — audit/measure runs show tree + document only, no reserved space for a chat panel.
- **Both side panels are fixed-width collapse/expand only** — no drag-to-resize. Collapsed state persists per browser via the existing [`sessionStorage.ts`](../../../_client/src/lib/sessionStorage.ts) helper, keyed by run slug, so a collapsed panel stays collapsed across reloads for that run.
- **Clicking a file in the tree navigates to that file's owning stage** (`/runs/{slug}/stages/{stage}`), the same route change a rail click already produces — there is no separate "view a file without changing stage" mode. The owning stage is found client-side by longest-prefix match of the clicked path against `run.data.stages[].file`; no new field is needed since that mapping already exists in `RunDetail`. A locked stage's files appear in the tree (so the run's shape is visible) but aren't clickable-through, mirroring the rail's existing lock behavior.
- **One new backend endpoint, nothing else changes:** `GET /runs/{slug}/tree`, sitting next to `get_file`/`put_file` in [`main.py`](../../../_server/app/main.py). No new scope rules, no write path — it's a read-only mirror of what `get_file` already permits, as a directory listing instead of a content fetch.

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ ECBD   runs ▾ / stage 03                              [+ New run]│  <- header, unchanged
├──────────────────────────────────────────────────────────────────┤
│  01 ✓ ── 02 ✓ ── 03 ● ── 04 (lock) ── 05 ── 06 ── 07 ── 08        │  <- stage rail, now horizontal
├───────────┬────────────────────────────────────┬─────────────────┤
│ ▸ 01_...  │ [Review banner — ready_for_review]  │ 💬 chat panel   │
│ ▸ 02_...  │ 03_content.md                       │ (design only,   │
│ ▾ 03_...  │ <document content, editable>        │  collapsible)   │
│    a.md   │                                      │                 │
│    b.md   │                                      │                 │
│ ▸ 04_...  │                                      │                 │
│ (collapse)│                                      │                 │
└───────────┴────────────────────────────────────┴─────────────────┘
```

- **Stage rail** (new full-width row): unchanged data source (`GET /runs/:slug`'s stage table) and gating logic; only orientation changes. Dots connect left-to-right instead of top-to-bottom.
- **File tree** (left, new): fetched via `GET /runs/:slug/tree`, rendered as a nested disclosure tree. Directories expand/collapse independently of the panel's own collapse toggle. No inline preview in the tree itself — clicking always routes to the owning stage, which renders the file in the existing document pane.
- **Document pane** (center): unchanged — same `DocumentPane` component, same edit/preview toggle, same save flow.
- **Chat panel** (right, was bottom drawer): same `ChatDrawer` component and the same session-start/transcript/send behavior; only the outer chrome changes from a bottom-docked, full-width, `max-height`-limited drawer to a right-docked, fixed-width column that fills the available height.
- **Review banner, diff view, reject dialog**: unchanged, still rendered inside the document pane above/around the file content exactly as today.

## Backend: `GET /runs/{slug}/tree`

```python
@app.get("/runs/{slug}/tree")
def get_tree(slug: str) -> dict[str, Any]:
    run_root = repo_root / "worksheets" / slug
    if not run_root.exists():
        raise HTTPException(404, f"run '{slug}' does not exist")
    return {"tree": _build_tree(run_root, run_root)}
```

`_build_tree` walks recursively, sorted directories-first-then-name, returning nodes shaped `{"name": str, "path": str, "is_dir": bool, "children": [...] | None}` where `path` is always relative to `run_root` (matching the `file_path` convention `get_file`/`put_file` already use, so a tree node's `path` can be passed straight to `GET /runs/:slug/files/:path` with no translation). Hidden files (dotfiles) and `.sessions/` are skipped — they're implementation state, not worksheet content a person browses. Reuses the same "no path can escape `run_root`" property `_resolve_run_file` already guarantees, trivially true here since the walk only ever descends from `run_root` itself.

## Frontend changes

- **New `FileTree` component** (`_client/src/components/FileTree.tsx`): fetches `GET /runs/:slug/tree` via a new `useRunTree(slug)` query, renders nested `<details>`/`<summary>` disclosure nodes (matching the existing disclosure pattern already used for tool-activity lines in `TranscriptView`), highlights the node matching the current stage's file.
- **`StagePage.tsx`**: body grid changes from `[rail][document]` to a new full-width row (`StageRail`, horizontal) above `[FileTree][document][ChatDrawer]`. File-click-to-stage-navigation logic (prefix match against `run.data.stages`) lives here, next to the existing reject/approve navigation logic it parallels.
- **`StageRail.tsx`**: same component, new CSS variant (`stage-rail--horizontal` or equivalent) — the connector element switches from a vertical bar to a horizontal one; no changes to `isStageUnlocked`, `stageName`, or the props contract.
- **`ChatDrawer.tsx`**: no internal changes; only the wrapping CSS class changes (from bottom-drawer styling to a right-panel column), so `chat-drawer__toggle`'s label copy ("Expand chat" / "Collapse chat") stays accurate.
- **`sessionStorage.ts`**: add two boolean keys per run (`fileTreeCollapsed`, `chatPanelCollapsed`), read on mount, written on toggle — same storage mechanism already used for session IDs, just a new key shape.

## Out of scope

- Resizable panel widths (explicitly deferred — fixed width, collapse/expand only).
- Any change to what stages gate on, how approval works, or the diff/reject flow.
- A dock-position toggle for the chat panel (right-only, no "move to bottom" control).
- An inert/placeholder chat panel for audit/measure runs — that space simply isn't reserved for those modes.
- In-tree file previews, drag/drop, rename, delete, or any tree-driven write operation — the tree is read-only navigation; all edits still go through `DocumentPane`'s existing save flow.

## Testing

- **Backend**: new tests for `GET /runs/{slug}/tree` — empty run, nested directories, a run that doesn't exist (404), and confirming no dotfiles/`.sessions/` leak into the response. Follows the existing fixture/style in `_server/tests/test_api.py`.
- **Frontend**: a `FileTree.test.tsx` covering nested rendering and click-to-navigate; updated `StagePage.test.tsx` and `StageRail.test.tsx` covering the horizontal rail variant and the new grid composition; a `sessionStorage.test.ts` addition for the two new collapse keys.
