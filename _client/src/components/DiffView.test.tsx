import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DiffView } from "./DiffView";

const sampleDiff = [
  "--- 01_intended-use.md (session start)",
  "+++ 01_intended-use.md (current)",
  "@@ -0,0 +1 @@",
  "+the intended use, spelled out",
].join("\n");

describe("DiffView", () => {
  it("marks added lines and leaves headers unmarked", () => {
    render(<DiffView diff={sampleDiff} />);
    const added = screen.getByText("+the intended use, spelled out");
    expect(added).toHaveClass("diff-view__line--added");

    const header = screen.getByText("+++ 01_intended-use.md (current)");
    expect(header).not.toHaveClass("diff-view__line--added");
  });
});
