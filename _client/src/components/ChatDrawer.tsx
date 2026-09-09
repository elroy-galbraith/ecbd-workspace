import { useState } from "react";
import { useSendMessage } from "../api/mutations";
import { useSession } from "../api/queries";
import { ApiError } from "../api/client";
import { clearSessionId, loadSessionId, storeSessionId } from "../lib/sessionStorage";
import { TranscriptView } from "./TranscriptView";

interface ChatDrawerProps {
  runKey: string;
  stage: string;
  startSession: (brief: string) => Promise<{ session_id: string }>;
  onSessionId?: (sessionId: string) => void;
}

export function ChatDrawer({ runKey, stage, startSession, onSessionId }: ChatDrawerProps) {
  const [sessionId, setSessionId] = useState<string | null>(() => loadSessionId(runKey, stage));
  const [collapsed, setCollapsed] = useState(true);
  const [draft, setDraft] = useState("");
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  const session = useSession(sessionId ?? undefined);
  const sendMessage = useSendMessage(sessionId ?? "", runKey);

  const sessionGone = session.isError && session.error instanceof ApiError && session.error.status === 404;

  async function handleStart() {
    setStarting(true);
    setStartError(null);
    try {
      const { session_id } = await startSession(draft);
      storeSessionId(runKey, stage, session_id);
      setSessionId(session_id);
      setDraft("");
      setCollapsed(false);
      onSessionId?.(session_id);
    } catch (err) {
      setStartError(err instanceof Error ? err.message : "failed to start session");
    } finally {
      setStarting(false);
    }
  }

  async function handleSend() {
    if (!draft.trim()) return;
    await sendMessage.mutateAsync(draft);
    setDraft("");
  }

  function handleForget() {
    clearSessionId(runKey, stage);
    setSessionId(null);
  }

  if (sessionId === null || sessionGone) {
    return (
      <div className="chat-drawer chat-drawer--empty">
        {sessionGone && <p role="alert">Previous session is no longer available — start a new one.</p>}
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Say what you need for this stage..."
        />
        <button onClick={handleStart} disabled={starting || !draft.trim()}>
          {starting ? "Starting…" : "Start"}
        </button>
        {startError && <p role="alert">{startError}</p>}
      </div>
    );
  }

  return (
    <div className={`chat-drawer${collapsed ? " chat-drawer--collapsed" : ""}`}>
      <button onClick={() => setCollapsed((c) => !c)}>{collapsed ? "💬 Expand chat" : "Collapse chat"}</button>
      {!collapsed && (
        <>
          {session.data && <TranscriptView entries={session.data.transcript} />}
          <textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Reply..." />
          <button onClick={handleSend} disabled={sendMessage.isPending || !draft.trim()}>
            {sendMessage.isPending ? "Thinking…" : "Send"}
          </button>
          {sendMessage.isError && (
            <p role="alert">{sendMessage.error instanceof Error ? sendMessage.error.message : "send failed"}</p>
          )}
          <button onClick={handleForget}>Forget session</button>
        </>
      )}
    </div>
  );
}
