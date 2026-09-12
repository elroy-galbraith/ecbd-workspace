The orchestration backend for the web-app version of this workspace. Not
part of any pipeline run — factory, like `_tools/`, not product.

Read `docs/decisions/2026-09-09-orchestration-backend.md` before touching
this folder; it explains the design this code implements, including two
choices that aren't obvious from the code alone: worksheet content is
never committed to git, and the server binds to localhost only.

Run tests from this directory: `python -m pytest tests/`.

Run the server from this directory: `python -m app.main`. (Running it as
`python app/main.py` fails — `main.py` uses package-relative imports, so
it only works invoked as a module.) It binds to `127.0.0.1` only, on port
8000 — that bind is load-bearing, not incidental (see the decision record
above).

`app/env.py` reads `ANTHROPIC_API_KEY` from a `.env` at the repo root, or
from the main checkout's `.env` when the repo root is a git worktree. It
runs from `main.py`'s `__main__` block only, so `create_app()` in a test
never touches the real environment. The README's "Running the web app"
section is the setup path a person follows.
