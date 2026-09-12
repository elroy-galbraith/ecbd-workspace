import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useRuns } from "../api/queries";
import { useStartRun } from "../api/mutations";
import { api } from "../api/client";
import type { RunSummary } from "../api/types";
import { ChatDrawer } from "../components/ChatDrawer";
import { clearSessionId, storeSessionId } from "../lib/sessionStorage";

const AUTO_CHECK_INTERVAL_MS = 4000;

export function NewRunPage() {
  const { data: runsBeforeStart } = useRuns();
  const startRun = useStartRun();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [knownSlugs, setKnownSlugs] = useState<Set<string>>(new Set());
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);
  const navigate = useNavigate();
  const inFlight = useRef(false);

  function handleSessionStarted(id: string) {
    setSessionId(id);
    setKnownSlugs(new Set((runsBeforeStart ?? []).map((run) => run.slug)));
  }

  async function checkForNewRun(options: { silent?: boolean } = {}) {
    if (!sessionId || inFlight.current) return;
    inFlight.current = true;
    if (!options.silent) {
      setChecking(true);
      setCheckError(null);
    }
    try {
      const runs = await api.get<RunSummary[]>("/runs");
      const created = runs.find((run) => !knownSlugs.has(run.slug));
      if (created) {
        storeSessionId(created.slug, "01", sessionId);
        clearSessionId("new", "01");
        navigate(`/runs/${created.slug}/stages/01`);
      } else if (!options.silent) {
        setCheckError("No new run yet — keep chatting, then check again once it's created.");
      }
    } catch (err) {
      if (!options.silent) {
        setCheckError(err instanceof Error ? err.message : "failed to check for a new run");
      }
    } finally {
      inFlight.current = false;
      if (!options.silent) setChecking(false);
    }
  }

  const checkForNewRunRef = useRef(checkForNewRun);
  useEffect(() => {
    checkForNewRunRef.current = checkForNewRun;
  });

  // The run doesn't exist until the agent calls create_run mid-conversation,
  // so poll for it quietly in the background instead of relying on the user
  // to remember to click "Check for created run" before navigating away --
  // that manual step was the only thing linking this chat session to the
  // run it creates (see storeSessionId below), so missing it stranded the
  // session with no way to find its way back to an approve/reject control.
  useEffect(() => {
    if (!sessionId) return;
    const id = window.setInterval(() => {
      checkForNewRunRef.current({ silent: true });
    }, AUTO_CHECK_INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [sessionId]);

  return (
    <div className="page">
      <header className="page__topbar">
        <Link to="/" className="brand">
          <span className="brand__mark" aria-hidden="true" />
          ECBD
        </Link>
        <Link to="/" className="btn btn--ghost page__topbar-runs">
          Runs
        </Link>
      </header>
      <div className="new-run-page">
        <div className="new-run-page__intro">
          <h1>Start a design run</h1>
          <p>
            Pipeline: <span className="tag tag--accent">design</span> — the only one supported today
          </p>
        </div>
        <div className="panel new-run-page__composer">
          <ChatDrawer runKey="new" stage="01" startSession={(brief) => startRun.mutateAsync(brief)} onSessionId={handleSessionStarted} />
        </div>
        {sessionId && (
          <div className="new-run-page__check">
            <p className="new-run-page__watching muted small">
              Watching for the run to be created — you'll be taken to it automatically.
            </p>
            <button className="btn btn--ghost" onClick={() => checkForNewRun()} disabled={checking}>
              {checking ? "Checking…" : "Check for created run"}
            </button>
            {checkError && <p role="alert">{checkError}</p>}
          </div>
        )}
      </div>
    </div>
  );
}
