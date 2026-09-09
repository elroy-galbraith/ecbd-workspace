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
