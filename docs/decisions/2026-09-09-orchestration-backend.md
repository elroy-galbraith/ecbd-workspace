---
date: 2026-09-09
status: decided, not yet implemented
decision: orchestration backend for a web-app version of this workspace — git-backed files, per-stage conversational sessions, frontmatter-declared tool scope, direct Anthropic API
---

# Orchestration backend for a web app

## Context

Today, running a pipeline means opening Claude Code against this repo: it reads a stage's `CONTEXT.md`, does tool-mediated file I/O against the working tree, and a person reviews the diff directly in git before the next stage starts. Moving this to a web app means something other than Claude Code has to do that job — read a stage contract, run a model against it with the right tools, and hold the line at each human check.

This record covers **only the orchestration backend** — the piece that runs stages and enforces gates. A chat/document-editing frontend, an export step (worksheet → downloadable eval build or audit report), and any move to multi-model support via OpenRouter are separate sub-projects, each deferred to its own decision record once this one is built against.

## Decision

- **Localhost only.** The backend runs on your own machine; the browser talks to `localhost`. No auth needed — there's no network exposure to gate. This is load-bearing, not incidental: `worksheets/CONTEXT.md` already documents that run folders never leave your machine ("often client work or unreleased models"), and that guarantee only holds if the process reading and writing them also never leaves your machine. A cloud-hosted backend would silently break it.
- **Single user, no multi-tenancy.** No per-user isolation to design.
- **Git-backed *scaffold*, not git-backed runs.** `worksheets/*/` is gitignored on purpose (confirmed in `.gitignore` and `worksheets/CONTEXT.md`) — only `worksheets/_index/log.md` and the scaffold `CONTEXT.md` files are tracked. The backend must not commit anything inside a run folder. `RUN.md`'s stage table and loop-back table are the audit trail already, as plain files — no commit is needed for them to persist. The only commit the backend ever makes is the one-line append to `_index/log.md` that `create_run` performs.
- **Conversational per stage.** The model can ask a clarifying question mid-stage and wait for a reply, or chain tool calls autonomously to draft a file — same code path either way (see Conversation loop, below).
- **Tool scope is hard-enforced per stage**, not left to prompt discipline. A stage's `CONTEXT.md` gets a structured frontmatter block the backend parses into a `StageScope`; a path outside that scope is a tool error, not a suggestion the model can ignore.
- **Direct Anthropic API**, not OpenRouter. Native tool-use blocks, and prompt caching pays for itself since the contract text and shared references are identical across every run of a given stage.

## Architecture

```
                        ┌─────────────────────┐
                        │   Frontend (later     │
                        │   sub-project)         │
                        └──────────┬───────────┘
                                   │ HTTP/SSE
                        ┌──────────▼───────────┐
                        │   Stage Session API    │
                        │  (start/resume/send/   │
                        │   approve/reject/list) │
                        └──────────┬───────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
     ┌────────▼────────┐ ┌─────────▼────────┐ ┌─────────▼────────┐
     │ Contract Loader   │ │ Stage Runner      │ │ Log Index &        │
     │ (parses CONTEXT.md│ │ (conversation loop,│ │ Session Diff       │
     │  frontmatter →    │ │  tool dispatch,    │ │ (commits only      │
     │  StageScope)       │ │  Anthropic client) │ │  _index/log.md;    │
     │                    │ │                    │ │  diffs a stage's   │
     │                    │ │                    │ │  files against a  │
     │                    │ │                    │ │  session-start     │
     │                    │ │                    │ │  snapshot — never  │
     │                    │ │                    │ │  git, for runs)    │
     └────────┬────────┘ └─────────┬────────┘ └─────────┬────────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                        ┌──────────▼───────────┐
                        │  Scoped Filesystem     │
                        │  Tool (read/write/edit,│
                        │  enforces the resolved │
                        │  scope for this stage) │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │  Repo working tree     │
                        │  (worksheets/, _shared/│
                        │   _templates/, etc.)   │
                        └───────────────────────┘
```

Five independently-testable units: **Contract Loader** (contract → scope), **Scoped Filesystem Tool** (scope-enforced read/write/edit), **Stage Runner** (owns one stage's conversation and the Anthropic tool-use loop), **Log Index & Session Diff** (the one narrow place that touches git — appending to `_index/log.md` — plus a non-git diff of a stage's files against how they looked when the session opened), **Stage Session API** (the only thing a frontend talks to).

## Contract format: frontmatter + scope resolution

Each stage's `CONTEXT.md` gets a frontmatter block alongside its existing prose. The prose stays the human-facing contract; the frontmatter is what the backend parses. Paths are relative to a declared base (`repo` or `run`) rather than the prose's `../../` arithmetic:

```yaml
---
bootstrap: true          # true only for a pipeline's first stage — it creates the run folder
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
  - path: worksheets/_index/log.md
    relative_to: repo
    access: read-write
  - path: _templates/design-run/
    relative_to: repo
    access: read
    type: directory
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 01_intended-use.md
    relative_to: run
---
```

Three approaches were considered for turning a contract into an enforceable scope: parsing the existing prose heuristically (fragile — 14 stage contracts phrase Inputs differently, and conditionals like "if it exists" or a bare directory reference don't reduce to a file list reliably), two-phase runtime resolution (no file changes, but the resolution step itself becomes a thing that can get it wrong, and it's less auditable than a file you can read and diff), and structured frontmatter (chosen) — a one-time mechanical edit to existing contracts, in exchange for a scope that's deterministic and checkable by a person, which matches how this workspace already treats structure as documentation.

**Bootstrap is special-cased, not generalized.** Only a pipeline's first stage creates a run folder (copies `_templates/<pipeline>-run/`, appends to `_index/log.md`) — actions no other stage should ever perform. Rather than widening the general filesystem tool to cover this, it gets its own single-purpose `create_run(slug)` tool, offered only when `bootstrap: true`. The model never reads template directory contents directly; `create_run` consumes them internally.

Resolution happens at stage start: `repo`-relative paths resolve immediately; `run`-relative paths resolve once the run folder exists (already true for non-bootstrap stages, true after `create_run` fires for a bootstrap one). Missing `optional` paths are dropped silently; a missing required path stops the session with a loud error — a broken contract or a broken run should never be something the model is left to improvise around.

## Conversation loop & tools

| Tool | Scope | Notes |
|---|---|---|
| `read_file(path)` | any `inputs` path | for content not preloaded (see below), or re-reading its own draft |
| `write_file(path, content)` | `outputs` + read-write `inputs` | |
| `edit_file(path, old, new)` | same as `write_file` | precise diffs instead of full rewrites — the Git Layer's diff is what the human check actually reads |
| `create_run(slug)` | only when `bootstrap: true` | template copy + log-index append, atomic |
| `mark_ready_for_review()` | always | ticks the stage's `RUN.md` row — the model's signal that a draft exists, not the human's approval |

System prompt is split at a cache breakpoint: above it, the contract's Process/Outputs/Human-check prose plus `repo`-relative input content (identical across every run of this stage); below it, `run`-relative input content (`RUN.md`, prior stage outputs — changes every run). Directory-type inputs are never exposed as readable content; `create_run` handles them server-side.

The loop: call the model with transcript + tools, dispatch any `tool_use` blocks, append results, repeat until a text-only turn. A text-only turn is the single stop-and-wait point whether the model is asking a clarifying question or announcing it's done — which is what makes "conversational" and "autonomous drafting" the same code path.

An out-of-scope path request returns a tool **error**, surfaced to the model to self-correct *and* flagged in the UI as a visible boundary hit — worth keeping visible so an under-specified contract gets noticed rather than silently worked around forever.

## Persistence & resuming

Each stage session's transcript is `.sessions/<session-id>.jsonl` (one line per turn) at the repo root, **gitignored** — a top-level, session-id-keyed location rather than nested under the run folder, because a bootstrap session (stage 1) exists before its run folder does. This is resumability state, not a worksheet artefact, and conflating it with `RUN.md` would break this workspace's existing claim that `RUN.md` is the only file recording a run's state. Resume = reload the file, replay into memory, continue; nothing needs redoing since prior tool calls are already recorded as results.

The one race worth guarding: the contract invites direct human edits to the same files the model writes. Once `mark_ready_for_review()` fires, the Stage Runner stops accepting model-initiated writes to that stage's outputs until the human sends another message reopening it.

## Human-check gate & advancement

This is where the backend turns CLAUDE.md's stated rule — *nothing moves to the next stage until a person has read the output of the last one* — into an actual constraint:

1. `mark_ready_for_review()` ticks the row. No unlock yet.
2. UI shows the contract's Human check text plus a diff against how the file looked when this stage's session opened (a plain file snapshot, not git — worksheet content is never committed). From here: keep chatting, edit the file directly, or resolve —
   - **`approve_stage`**: validates every declared output exists and is non-empty, auto-ticks the row if the model never did, and — this is the part the model's own tools can never do — appends the stage number to an `approved_stages:` list in `RUN.md`'s frontmatter. **The Done tick and approval are deliberately two different facts in two different places of the same file.** The model can tick a row (via `mark_ready_for_review`) to say a draft exists; only `approve_stage` can extend `approved_stages`, and no tool exposed to a model conversation ever touches it. **Only a stage number's presence in `approved_stages` gates a session for stage N+1** — a model ticking its own row must never be sufficient on its own to unlock the next stage. Nothing here touches git.
   - **`reject_stage(target_stage, reason)`**: unticks the current stage and every stage back through `target_stage` inclusive, removes all of them from `approved_stages`, adds one `RUN.md` Loop-backs row. Reopening `target_stage`'s prior session (resuming its transcript) requires session rehydration from `.sessions/`, which is not yet built — see "Known gaps" below.

The system validates structure — files exist, scope respected, gate order enforced — never quality. That judgment is exactly what the human check is for.

## API surface

Localhost-only; no auth. Bind to `127.0.0.1`, never `0.0.0.0`.

| Endpoint | Purpose |
|---|---|
| `GET /runs` | list runs — backs the existing "asked for status" flow |
| `GET /runs/:slug` | parsed `RUN.md`: stage table, loop-backs, frontmatter |
| `POST /runs/:pipeline/start` | opens a bootstrap session with the initial brief |
| `POST /sessions/:id/messages` | send a chat message; response streamed (SSE) as text + tool-call events |
| `GET /sessions/:id` | resume: transcript + status |
| `POST /runs/:slug/stages/:stage/approve` | `approve_stage` |
| `POST /runs/:slug/stages/:stage/reject` | `reject_stage` |
| `GET`/`PUT /runs/:slug/files/:path` | document viewer/editor pane — scoped to that run folder, path-traversal guarded |
| `GET /runs/:slug/diff/:stage` | diff against the session-start snapshot, for the human-check view — plain file comparison, not git |

## Error handling

- Invalid/missing frontmatter → Contract Loader refuses to start the session. Fail closed, never fall back to unrestricted access.
- API errors mid-loop → transcript is appended incrementally, so a retry resumes cleanly rather than replaying or losing turns.
- Runaway tool-call loop → capped iterations per human turn (~30); on hitting it, stop and report rather than hang.
- `create_run` slug collision → reject, ask for a different slug.
- Conflicting access levels on the same path across two `inputs` entries → validated at load time as a contract lint failure, not discovered at runtime.

## Testing

- Contract Loader unit-tested against this repo's real `CONTEXT.md` files — doubles as a lint that fails if editing a stage contract breaks its frontmatter.
- Scoped Filesystem Tool unit-tested with fixture scopes: allowed paths succeed, disallowed error, optional-missing returns absent.
- Stage Runner loop tested with a mocked Anthropic client and scripted tool-use sequences: dispatch, transcript append, stop-on-text-turn, iteration cap.
- One end-to-end test per pipeline: a scripted stage-1 conversation against a sandboxed copy of the repo, asserting the run folder / `RUN.md` / log index land where expected — the test that actually proves the backend replicates current Claude-Code behavior.

## Consequences

- Every existing stage `CONTEXT.md` needs a frontmatter block added before this backend can run against it — mechanical, but touches all 14+ stage contracts across `01-design/` and `02-audit/` (and `03-measure/` if that pipeline is included later).
- A top-level `.sessions/` directory needs adding to `.gitignore`.
- The workspace's "loading discipline" rule moves from a norm you can watch enforced in a terminal to a technical constraint enforced in code — stricter than today's Claude Code sessions, which could technically read outside a contract's Inputs if the model chose to.
- Because the backend never commits worksheet content, there is no built-in recovery if you edit or delete a run folder by mistake — same as today. The backend does not change this workspace's existing stance that runs need a backup outside this repo if they matter; it must not invent one via git without you deciding that separately.
- Running localhost-only means this design carries no auth, no CORS hardening beyond the default same-origin behavior, and no concern for concurrent remote clients. If a later need ever pushes this off of localhost (e.g. onto a private home server), auth and network hardening become required additions — not covered by this record.

## What is not decided

- The frontend (chat + document viewer/editor) and the export step (worksheet → downloadable eval build or audit report) are separate sub-projects, not covered here.
- Whether `03-measure/`'s stages get the same frontmatter treatment, or whether that pipeline is out of scope for the web app's first version.
- Whether to eventually support OpenRouter for per-stage model choice (e.g. a cheaper model for the mechanical stages 3–6). Direct Anthropic API is the starting point; nothing here forecloses adding a provider-abstraction layer later if that need becomes concrete.

## Known gaps against this record (first implementation pass)

The first implementation (see `docs/superpowers/plans/2026-09-09-orchestration-backend-plan.md` and its SDD ledger) built the `01-design` pipeline end to end, but the final whole-branch review found this record describes a few things the code doesn't yet do. Recorded here so the gap is explicit rather than discovered by surprise later:

- **Session resumption isn't implemented.** `.sessions/<id>.jsonl` is written incrementally as designed, but nothing rehydrates a `StageRunner` from it — `GET /sessions/:id` only works against the in-process session that created it, and is lost on a server restart. §Persistence & resuming describes the target; the rehydrate path itself is unbuilt.
- **`reject_stage` doesn't reopen the target stage's session** (it correctly rewrites `RUN.md`, but resuming `target_stage`'s prior transcript depends on the same rehydration path above).
- **No `list_files` tool for directory-scoped inputs.** A stage whose contract declares a directory input (e.g. `08_build`'s `build/`, written by stages 3–6) has no way to enumerate what's in it — only to read a file it already knows the name of. Not exercised by this pass's tests, which stop at stage 2; needed before stage 08 is actually runnable through this backend.

These three are scope decisions, not defects — each was deliberately left out of the first implementation pass's single fix wave rather than rushed in unreviewed. First candidates for the next plan against this record.
