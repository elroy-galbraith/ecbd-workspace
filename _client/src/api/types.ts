export interface RunSummary {
  slug: string;
  mode: string;
  subject: string;
  opened: string;
}

export interface StageTableRow {
  file: string;
  stage: string;
  questions: string;
  done: boolean;
}

export interface LoopBack {
  date: string;
  from_stage: string;
  back_to_stage: string;
  forced_by: string;
  what_changed: string;
}

export interface RunDetail {
  slug: string;
  status: string | null;
  opened: string | null;
  closed: string | null;
  approved_stages: string[];
  stages: StageTableRow[];
  loop_backs: LoopBack[];
}

export type TranscriptBlock =
  | { type: "text"; text: string }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; content: string; is_error: boolean };

export interface TranscriptEntry {
  role: "user" | "assistant";
  content: TranscriptBlock[];
}

export interface SessionState {
  transcript: TranscriptEntry[];
  ready_for_review: boolean;
}

export interface FileContent {
  path: string;
  content: string;
}

export interface DiffResponse {
  diff: string;
}

export interface ApproveResponse {
  approved_stage: string;
  approved_outputs: string[];
}
