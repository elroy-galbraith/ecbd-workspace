import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TranscriptView, toRenderLines } from "./TranscriptView";
import type { TranscriptEntry } from "../api/types";

const entries: TranscriptEntry[] = [
  { role: "user", content: [{ type: "text", text: "let's start" }] },
  {
    role: "assistant",
    content: [
      { type: "tool_use", id: "t1", name: "write_file", input: { path: "01_intended-use.md", content: "..." } },
    ],
  },
  {
    role: "user",
    content: [{ type: "tool_result", tool_use_id: "t1", content: "wrote 01_intended-use.md", is_error: false }],
  },
  {
    role: "assistant",
    content: [{ type: "tool_use", id: "t2", name: "read_file", input: { path: "does-not-exist.md" } }],
  },
  {
    role: "user",
    content: [{ type: "tool_result", tool_use_id: "t2", content: "'does-not-exist.md' does not exist", is_error: true }],
  },
  { role: "assistant", content: [{ type: "text", text: "drafted, ready for review" }] },
];

describe("toRenderLines", () => {
  it("pairs tool_use with its tool_result and keeps text lines separate", () => {
    const lines = toRenderLines(entries);
    expect(lines).toEqual([
      { kind: "text", role: "user", text: "let's start" },
      {
        kind: "tool",
        name: "write_file",
        input: { path: "01_intended-use.md", content: "..." },
        result: "wrote 01_intended-use.md",
        isError: false,
      },
      {
        kind: "tool",
        name: "read_file",
        input: { path: "does-not-exist.md" },
        result: "'does-not-exist.md' does not exist",
        isError: true,
      },
      { kind: "text", role: "assistant", text: "drafted, ready for review" },
    ]);
  });
});

describe("TranscriptView", () => {
  it("flags an error tool result distinctly", () => {
    render(<TranscriptView entries={entries} />);
    const errorLine = screen.getByText(/read_file/).closest("details");
    expect(errorLine).toHaveClass("transcript__activity--error");

    const okLine = screen.getByText(/write_file/).closest("details");
    expect(okLine).not.toHaveClass("transcript__activity--error");
  });
});
