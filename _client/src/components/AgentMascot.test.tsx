import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AgentMascot, getAgentActivity } from "./AgentMascot";
import type { TranscriptEntry } from "../api/types";

describe("getAgentActivity", () => {
  it("is idle when there is no transcript yet", () => {
    expect(getAgentActivity([])).toEqual({ pose: "idle", label: "thinking…" });
  });

  it("is idle when the last entry is a resolved tool result (waiting on the next model turn)", () => {
    const entries: TranscriptEntry[] = [
      { role: "user", content: [{ type: "text", text: "go" }] },
      {
        role: "assistant",
        content: [{ type: "tool_use", id: "t1", name: "read_file", input: { path: "01.md" } }],
      },
      {
        role: "user",
        content: [{ type: "tool_result", tool_use_id: "t1", content: "hello", is_error: false }],
      },
    ];
    expect(getAgentActivity(entries)).toEqual({ pose: "idle", label: "thinking…" });
  });

  it("is reading when the last entry is an unresolved read_file call", () => {
    const entries: TranscriptEntry[] = [
      {
        role: "assistant",
        content: [{ type: "tool_use", id: "t1", name: "read_file", input: { path: "01_intended-use.md" } }],
      },
    ];
    expect(getAgentActivity(entries)).toEqual({ pose: "reading", label: "reading 01_intended-use.md" });
  });

  it("is writing when the last entry is an unresolved write_file call", () => {
    const entries: TranscriptEntry[] = [
      {
        role: "assistant",
        content: [{ type: "tool_use", id: "t1", name: "write_file", input: { path: "02_capability.md", content: "..." } }],
      },
    ];
    expect(getAgentActivity(entries)).toEqual({ pose: "writing", label: "writing 02_capability.md" });
  });

  it("treats edit_file, create_run, and mark_ready_for_review as writing too", () => {
    const withCall = (name: string, input: Record<string, unknown>): TranscriptEntry[] => [
      { role: "assistant", content: [{ type: "tool_use", id: "t1", name, input }] },
    ];
    expect(getAgentActivity(withCall("edit_file", { path: "01.md", old: "a", new: "b" })).pose).toBe("writing");
    expect(getAgentActivity(withCall("create_run", { slug: "s", subject: "s" })).pose).toBe("writing");
    expect(getAgentActivity(withCall("mark_ready_for_review", {})).pose).toBe("writing");
  });

  it("falls back to a plain label when the tool call has no path input", () => {
    const entries: TranscriptEntry[] = [
      { role: "assistant", content: [{ type: "tool_use", id: "t1", name: "mark_ready_for_review", input: {} }] },
    ];
    expect(getAgentActivity(entries)).toEqual({ pose: "writing", label: "writing" });
  });

  it("is idle when the last entry is assistant text with no tool call", () => {
    const entries: TranscriptEntry[] = [{ role: "assistant", content: [{ type: "text", text: "drafted" }] }];
    expect(getAgentActivity(entries)).toEqual({ pose: "idle", label: "thinking…" });
  });
});

describe("AgentMascot", () => {
  it("renders the activity label", () => {
    render(<AgentMascot activity={{ pose: "reading", label: "reading 01_intended-use.md" }} />);
    expect(screen.getByText("reading 01_intended-use.md")).toBeInTheDocument();
  });

  it("marks the root element with the current pose", () => {
    const { container } = render(<AgentMascot activity={{ pose: "writing", label: "writing 02.md" }} />);
    expect(container.querySelector(".agent-mascot--writing")).toBeInTheDocument();
  });
});
