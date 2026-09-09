import type { TranscriptEntry } from "../api/types";

interface TranscriptViewProps {
  entries: TranscriptEntry[];
}

interface TextLine {
  kind: "text";
  role: "user" | "assistant";
  text: string;
}

interface ToolLine {
  kind: "tool";
  name: string;
  input: Record<string, unknown>;
  result: string;
  isError: boolean;
}

export type RenderLine = TextLine | ToolLine;

export function toRenderLines(entries: TranscriptEntry[]): RenderLine[] {
  const lines: RenderLine[] = [];
  const pendingToolUse = new Map<string, { name: string; input: Record<string, unknown> }>();

  for (const entry of entries) {
    for (const block of entry.content) {
      if (block.type === "text") {
        lines.push({ kind: "text", role: entry.role, text: block.text });
      } else if (block.type === "tool_use") {
        pendingToolUse.set(block.id, { name: block.name, input: block.input });
      } else if (block.type === "tool_result") {
        const use = pendingToolUse.get(block.tool_use_id);
        lines.push({
          kind: "tool",
          name: use?.name ?? "unknown tool",
          input: use?.input ?? {},
          result: block.content,
          isError: block.is_error,
        });
        pendingToolUse.delete(block.tool_use_id);
      }
    }
  }
  return lines;
}

function toolIcon(name: string): string {
  if (name === "write_file" || name === "edit_file") return "📝";
  if (name === "read_file") return "📖";
  if (name === "create_run") return "🗂️";
  if (name === "mark_ready_for_review") return "✅";
  return "🔧";
}

export function TranscriptView({ entries }: TranscriptViewProps) {
  const lines = toRenderLines(entries);
  return (
    <div className="transcript">
      {lines.map((line, index) => {
        if (line.kind === "text") {
          return (
            <p key={index} className={`transcript__bubble transcript__bubble--${line.role}`}>
              {line.text}
            </p>
          );
        }
        const path = typeof line.input.path === "string" ? line.input.path : undefined;
        return (
          <details
            key={index}
            className={`transcript__activity${line.isError ? " transcript__activity--error" : ""}`}
          >
            <summary>
              {toolIcon(line.name)} {line.name}
              {path ? ` \`${path}\`` : ""}
            </summary>
            <pre>{line.result}</pre>
          </details>
        );
      })}
    </div>
  );
}
