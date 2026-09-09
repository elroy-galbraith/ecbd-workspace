The orchestration backend for the web-app version of this workspace. Not
part of any pipeline run — factory, like `_tools/`, not product.

Read `docs/decisions/2026-09-09-orchestration-backend.md` before touching
this folder; it explains the design this code implements, including two
choices that aren't obvious from the code alone: worksheet content is
never committed to git, and the server binds to localhost only.

Run tests from this directory: `python -m pytest tests/`.
