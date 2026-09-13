import type { TranscriptEntry } from "../api/types";

export type AgentPose = "idle" | "reading" | "writing";

export interface AgentActivity {
  pose: AgentPose;
  label: string;
}

const WRITE_TOOLS = new Set(["write_file", "edit_file", "create_run", "mark_ready_for_review"]);

export function getAgentActivity(entries: TranscriptEntry[]): AgentActivity {
  const last = entries[entries.length - 1];
  const pendingCall = last?.role === "assistant" ? last.content.find((b) => b.type === "tool_use") : undefined;

  if (!pendingCall) return { pose: "idle", label: "thinking…" };

  const path = typeof pendingCall.input.path === "string" ? pendingCall.input.path : undefined;
  if (pendingCall.name === "read_file") {
    return { pose: "reading", label: path ? `reading ${path}` : "reading" };
  }
  if (WRITE_TOOLS.has(pendingCall.name)) {
    return { pose: "writing", label: path ? `writing ${path}` : "writing" };
  }
  return { pose: "idle", label: "thinking…" };
}

interface AgentMascotProps {
  activity: AgentActivity;
}

function MascotFace({ pose }: { pose: AgentPose }) {
  return (
    <svg width={22} height={22} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <circle cx="10" cy="10.5" r="6.5" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="7.6" cy="9.5" r="0.9" fill="currentColor" />
      <circle cx="12.4" cy="9.5" r="0.9" fill="currentColor" />
      {pose === "reading" && (
        <path d="M6 14.2c1.4-.7 2.9-.7 4 0M10 14.2c1.1-.7 2.6-.7 4 0" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      )}
      {pose === "writing" && <path d="M13.2 12.3l2.3-2.3.9.9-2.3 2.3-1.2.3.3-1.2Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />}
      {pose === "idle" && <path d="M7.5 13.4a3 3 0 0 0 5 0" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />}
    </svg>
  );
}

export function AgentMascot({ activity }: AgentMascotProps) {
  return (
    <div className={`agent-mascot agent-mascot--${activity.pose}`}>
      <span className="agent-mascot__face">
        <MascotFace pose={activity.pose} />
      </span>
      <span className="agent-mascot__label">{activity.label}</span>
    </div>
  );
}
