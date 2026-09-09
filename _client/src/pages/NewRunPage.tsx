import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRuns } from "../api/queries";
import { useStartRun } from "../api/mutations";
import { api } from "../api/client";
import type { RunSummary } from "../api/types";
import { ChatDrawer } from "../components/ChatDrawer";
import { clearSessionId, storeSessionId } from "../lib/sessionStorage";

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
        clearSessionId("new", "01");
        navigate(`/runs/${created.slug}/stages/01`);
      } else {
        setCheckError("No new run yet — keep chatting, then check again once it's created.");
      }
    } catch (err) {
      setCheckError(err instanceof Error ? err.message : "failed to check for a new run");
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
