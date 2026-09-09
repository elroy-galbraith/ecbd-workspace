---
date: 2026-09-09
status: approved, not yet implemented
decision: React + Vite + TypeScript frontend for the orchestration backend — full stage loop (run list, start, per-stage chat, document viewer, diff, approve/reject) for the 01-design pipeline
---

# Orchestrator frontend

## Context

`docs/decisions/2026-09-09-orchestration-backend.md` built the orchestration backend — a localhost-only FastAPI service that runs a design-pipeline stage as a conversational session against the Anthropic API, enforces per-stage tool scope, and holds the human-check gate via `approve_stage`/`reject_stage`. That record explicitly deferred "a chat/document-editing frontend" as a separate sub-project. This record covers that frontend.

The backend's actual behavior differs from its own decision record in a few ways worth designing against directly rather than around:

- `POST /sessions/:id/messages` is **synchronous** — it blocks until the model's turn ends (a text-only turn, possibly after several tool calls) and returns `{"reply": <final text>}`. There is no SSE streaming today, despite the backend record mentioning it as the target.
- Session state is **in-memory only** (`sessions: dict[str, StageRunner]` in `_server/app/main.py`) — a server restart loses every active session. `GET /sessions/:id` only works against the process that created it; there is no rehydration path from the `.sessions/*.jsonl` transcripts yet.
- Only the `design` pipeline's `start` route is wired up (`POST /runs/{pipeline}/start` rejects anything but `"design"`).
- `reject_stage` correctly rewrites `RUN.md` but cannot reopen the target stage's prior session, for the same rehydration-gap reason.
- Two routes the backend record's own API table lists as part of the surface were never actually implemented: `GET /runs/:slug` (parsed `RUN.md`) and `GET`/`PUT /runs/:slug/files/:path` (document viewer/editor). This is different from the gaps above — those are documented shortfalls of a real design; these two are just missing code for a design that was already agreed.

This frontend is built **frontend-only against every already-agreed part of the backend's API surface** — no new backend design happens here. The one exception is finishing the two routes above: since they're already fully specified in `docs/decisions/2026-09-09-orchestration-backend.md`'s API table and the stage rail and document pane cannot exist without them, this plan implements exactly what that table already specifies, as a small prerequisite, rather than redesigning the frontend around their absence. Where the backend's real behavior falls short of its own decision record in ways that *would* require new design to fix (no streaming, no resumption), the frontend degrades honestly instead.

## Decision

- **Scope: the full stage loop, one pipeline.** Run list, start a new `design` run, per-stage chat, document viewer with diff, approve/reject — the complete loop end to end, for `01-design` only. Not a read-only dashboard slice, not a chat-only slice.
- **Stack: React + Vite + TypeScript.** A standard SPA toolchain — fast dev server, good fit for a chat UI plus a document viewer with local component state, and the easiest base to extend later (streaming, multi-pipeline, session resumption) without a rewrite.
- **Data fetching: `@tanstack/react-query`.** Every mutation (send message, approve, reject, save a file edit) invalidates the relevant query so the UI reflects the backend's actual file/session state rather than an optimistic guess — important given the backend has no push channel to correct a wrong guess later.
- **Routing: `react-router`.**
- **Backend: finish two already-specified endpoints, change nothing else.** `GET /runs/:slug` and `GET`/`PUT /runs/:slug/files/:path` are implemented exactly as `docs/decisions/2026-09-09-orchestration-backend.md`'s API table already describes them, plus CORS opened for the frontend's dev-server origin. No other backend behavior changes, and no new backend design decisions are made — the rest of the documented API surface is a fixed contract for this sub-project.

## Screens & routes

| Route | Purpose |
|---|---|
| `/` | Run list — `GET /runs` rendered as a table (slug, mode, subject, opened), each row linking to its current stage. A "New run" button. |
| `/runs/new` | Start form: pipeline fixed to `design` (the only one the backend accepts), a brief textarea, submits to `POST /runs/design/start`. Since `create_run` only fires mid-conversation once the model calls it, this route is really "stage 01, no run/slug yet" — the resulting session renders in the same stage-screen UI before a slug exists. |
| `/runs/:slug/stages/:stage` | The main screen (see Layout, below). |

`/runs/:slug` (no stage) redirects to whatever stage `GET /runs/:slug` reports as current (first non-approved stage in `_STAGE_ORDER`, or the last one if all approved).

## Layout (main stage screen)

Document-first, two-column, chat as a bottom drawer — chosen over a three-column always-visible-chat layout and a fully tabbed single pane, because the document is what you spend the most time reading and a drawer keeps it full-width without losing the conversation.

```
┌─────────────────────────────────────────────────────────┐
│ ☰ runs ▾   design-faithfulness-summarization | stage 02  │
├───────────┬─────────────────────────────────────────────┤
│ 01 ✓      │  [Review banner — only when ready_for_review]│
│ 02 ●      │  02_capability.md                            │
│ 03 (lock) │  <document content, editable>                │
│ ...       │                                               │
├───────────┴─────────────────────────────────────────────┤
│ 💬 chat drawer (collapsed by default; tap to expand)      │
└─────────────────────────────────────────────────────────┘
```

- **Stage rail** (left): parsed from `GET /runs/:slug`'s stage table. Approved stages and the current stage are clickable; later stages are locked (unclickable, visibly dimmed) until the one before them is approved — mirrors the backend's own `stage_is_approved` gate on `POST /runs/:slug/stages/:stage/start`, so the UI never offers an action the backend would 404.
- **Run switcher** (top bar): a dropdown, not a persistent list — this is a single-user local tool where run count stays small; a dropdown is enough and keeps the document pane's width.
- **Document pane** (center): the file named in the current stage's `RUN.md` row (the stage table's `File` column — `parse_run_md` already surfaces this, so the frontend never needs the CONTEXT.md contract's `outputs` directly). A directory-shaped entry (`build/` for stage 08) shows a plain notice instead of an editor — no enumeration tool exists yet (a known backend gap), so there's nothing meaningful to fetch. Fetched via `GET /runs/:slug/files/:path`, editable inline, saved via explicit `PUT` — a direct alternative to asking the model to write it, matching the backend record's own framing ("keep chatting, edit the file directly, or resolve"). The `PUT` endpoint refuses an edit to `RUN.md` that would change `approved_stages` (mirroring the existing model-tool guard in `_server/app/fs_tool.py`) — that fact stays exclusively `approve_stage`/`reject_stage`'s to write, whether the write comes from the model or a direct human edit.
- **Chat drawer** (bottom): collapsed by default, expands to show the transcript and an input. Collapsing it doesn't stop anything server-side — it's a viewport choice, not a session state.

### Review banner

Appears in the document pane **only when** `GET /sessions/:id` reports `ready_for_review: true` — no review chrome exists before that point, so the screen stays quiet while a draft is still being written. Holds:

- **View diff** — `GET /runs/:slug/diff/:stage`, rendered as the unified-diff text it already is (monospace, `+`/`-` line coloring, no diff library needed since the backend computes it with `difflib.unified_diff`).
- **Approve** — `POST /runs/:slug/stages/:stage/approve`, then invalidate the run query and advance the stage rail.
- **Reject…** — opens a small dialog: a dropdown of already-approved stages (valid `target_stage` values — rejecting to a stage that was never approved doesn't make sense), a free-text reason, submits `POST /runs/:slug/stages/:stage/reject`. After rejection, the UI reflects that `target_stage` through the current stage are unticked and un-approved; per the backend's known gap, it does **not** attempt to reopen `target_stage`'s prior chat session — it shows a plain "stage reopened, start a new session" state instead of pretending to resume one.

## Chat transcript rendering

`GET /sessions/:id` returns the full transcript as `{role, content: [...]}` entries (`text`, `tool_use`, `tool_result` blocks — see `_server/app/stage_runner.py`'s `_blocks_to_dicts`). Rendering rules:

- `text` blocks render as normal chat bubbles (user vs. assistant).
- A `tool_use` block and its matching `tool_result` collapse into one compact activity line — e.g. "📝 wrote `02_capability.md`", "📖 read `RUN.md`" — expandable on click to see the raw arguments/content, not shown inline by default.
- A `tool_result` with `is_error: true` renders as a visually distinct flagged line (not just another grey activity row) — this is the UI's realization of the backend record's intent that an out-of-scope path request "surfaces... flagged in the UI as a visible boundary hit," worth noticing rather than silently retried away.
- Sending a message (`POST /sessions/:id/messages`) shows a "thinking…" state in the drawer for the duration of the request — this is a real synchronous wait, sometimes tens of seconds across several chained tool calls, not a network blip.
- After a send resolves, the frontend **refetches the full transcript** (`GET /sessions/:id`) rather than trusting only the returned `reply` string — tool activity that happened mid-turn only shows up in the full transcript, and the compact activity lines above depend on it.

## Session persistence across page refresh

Session IDs live only in backend memory and there's no server-side resumption path yet. The frontend stores `{slug}/{stage} → session_id` in `localStorage` so a **page refresh** (not a backend restart) doesn't orphan an in-progress chat — reload the page, look up the stored ID, call `GET /sessions/:id` to rehydrate the transcript. If that 404s (backend restarted, ID no longer known), the UI falls back to a plain "this session is gone — start a new one for this stage" state rather than pretending resumption succeeded. This is a page-refresh convenience only; it does not close the backend's actual resumption gap.

## Error handling

- All data fetching goes through React Query; a failed query or mutation drives an inline error banner in the relevant view (run list, stage screen, or chat drawer) — no global error boundary beyond a top-level catch for genuinely unexpected render crashes.
- API error bodies (502 truncated-response, 400 contract/approval error, 404 unknown session/run/stage) are shown close to verbatim — this is a single-user local tool, and the backend's error text is already written for a person to read, not for a frontend to reinterpret.
- No retry-with-backoff or optimistic-UI magic: a failed mutation just fails visibly, and the person decides whether to resend.

## Configuration

- Backend base URL is a Vite env var (`VITE_API_BASE`), defaulting to `http://127.0.0.1:8000`. No other environment-specific config — this stays a two-process localhost tool (Vite dev server + FastAPI), not a deployed app.

## Testing

- Component tests (Vitest + React Testing Library) for: the stage rail (locked/unlocked/approved states from a fixture `RUN.md` table), the diff renderer (fixture unified-diff text), and the chat transcript renderer (fixture transcripts covering text-only, tool-activity, and `is_error` cases).
- No end-to-end test against a live backend in this pass — that requires running the Python server as well, which sits outside a frontend-only sub-project's boundary. (A follow-up could add one once both halves are stable enough to test together.)

## Consequences

- The frontend inherits every gap already recorded in the backend's own decision doc (no streaming, no session resumption, no `list_files` for directory-scoped outputs like `08_build`'s `build/`). None of those are fixed here; the frontend is written to degrade honestly against them rather than mask them.
- Because `08_build`'s directory-scoped output has no enumeration tool yet, that stage's document pane has nothing meaningful to show beyond whatever single files it can name directly — full stage-08 support is blocked on the backend gap, not on this frontend design.
- Editing a file directly via the document pane's `PUT` and the model editing the same file via `write_file`/`edit_file` are two paths to the same file with no locking between them — acceptable for a single-user local tool where both actions are the same person, but worth being aware of if that assumption ever changes.

## What is not decided

- Real-time streaming of the model's response (would require a backend change, explicitly out of scope for this sub-project).
- Session resumption after a backend restart (backend gap, not a frontend decision).
- Support for `02-audit` or `03-measure` pipelines in this UI — `01-design` only, for now; the backend itself only accepts `"design"` as a pipeline argument today.
