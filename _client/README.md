# _client

The browser front end for the orchestration backend in `_server/`. React, TypeScript and Vite.

Start it from this directory:

```bash
npm install
npm run dev
```

It serves on `http://localhost:5173` and expects the backend on `http://127.0.0.1:8000`. Start that first — see `_server/CONTEXT.md`. The full setup path, including the Anthropic API key, is the "Running the web app" section of the repo README.

Point it at a different backend with `VITE_API_BASE` in a `.env` file here; `.env.example` is the template. The backend's CORS allowlist only covers port 5173, so a front end on another port is refused.

```bash
npm test    # vitest
npm run lint    # oxlint
npm run build   # tsc -b && vite build
```

`CONTEXT.md` in this directory says what this app does and does not do, and points at the design spec.
