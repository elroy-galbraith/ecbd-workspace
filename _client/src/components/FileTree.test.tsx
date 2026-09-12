import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { FileTree, findOwningStage } from "./FileTree";
import type { RunTreeNode } from "../api/types";
import type { StageTableRow } from "../api/types";

const mockUseRunTree = vi.fn();
vi.mock("../api/queries", () => ({
  useRunTree: (...args: unknown[]) => mockUseRunTree(...args),
}));

const mockLoadPanelCollapsed = vi.fn();
const mockStorePanelCollapsed = vi.fn();
vi.mock("../lib/sessionStorage", () => ({
  loadPanelCollapsed: (...args: unknown[]) => mockLoadPanelCollapsed(...args),
  storePanelCollapsed: (...args: unknown[]) => mockStorePanelCollapsed(...args),
}));

const stages: StageTableRow[] = [
  { file: "01_intended-use.md", stage: "01", questions: "Q1-2", done: true },
  { file: "02_capability.md", stage: "02", questions: "Q3-5", done: false },
  { file: "08_build/", stage: "08", questions: "Q9", done: false },
];

const tree: RunTreeNode[] = [
  { name: "01_intended-use.md", path: "01_intended-use.md", is_dir: false, children: null },
  { name: "02_capability.md", path: "02_capability.md", is_dir: false, children: null },
  {
    name: "08_build",
    path: "08_build",
    is_dir: true,
    children: [{ name: "eval.jsonl", path: "08_build/eval.jsonl", is_dir: false, children: null }],
  },
  { name: "RUN.md", path: "RUN.md", is_dir: false, children: null },
];

beforeEach(() => {
  vi.clearAllMocks();
  mockLoadPanelCollapsed.mockReturnValue(null);
  mockUseRunTree.mockReturnValue({ data: { tree }, isLoading: false, isError: false });
});

describe("findOwningStage", () => {
  it("matches an exact file path", () => {
    expect(findOwningStage(stages, "01_intended-use.md")).toBe("01");
  });

  it("matches a file nested under a directory-shaped stage", () => {
    expect(findOwningStage(stages, "08_build/eval.jsonl")).toBe("08");
  });

  it("returns undefined for a path with no owning stage", () => {
    expect(findOwningStage(stages, "RUN.md")).toBeUndefined();
  });
});

describe("FileTree", () => {
  it("renders files as links to their owning stage", () => {
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={["01"]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    const stage2File = screen.getByRole("link", { name: /02_capability\.md/ });
    expect(stage2File).toHaveAttribute("href", "/runs/design-my-eval/stages/02");
  });

  it("renders a file whose stage is locked as disabled, not a link", () => {
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={[]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    const locked = screen.getByText("02_capability.md");
    expect(locked).toHaveAttribute("aria-disabled", "true");
    expect(screen.queryByRole("link", { name: /02_capability\.md/ })).not.toBeInTheDocument();
  });

  it("renders a file with no owning stage as inert", () => {
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={["01"]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    const inert = screen.getByText("RUN.md");
    expect(inert).toHaveAttribute("aria-disabled", "true");
    expect(screen.queryByRole("link", { name: /RUN\.md/ })).not.toBeInTheDocument();
  });

  it("renders a nested file under an expanded directory", () => {
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={["01", "02"]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /eval\.jsonl/ })).toHaveAttribute(
      "href",
      "/runs/design-my-eval/stages/08",
    );
  });

  it("toggles collapsed state and persists it", async () => {
    const { default: userEvent } = await import("@testing-library/user-event");
    render(
      <MemoryRouter>
        <FileTree slug="design-my-eval" stages={stages} approvedStages={["01"]} activeStage="01" gated={true} />
      </MemoryRouter>,
    );

    await userEvent.setup().click(screen.getByRole("button", { name: /collapse files/i }));
    expect(mockStorePanelCollapsed).toHaveBeenCalledWith("design-my-eval", "file-tree", true);
    expect(screen.getByRole("button", { name: /expand files/i })).toBeInTheDocument();
  });

  it("ungated (audit/measure) runs never render a locked file", () => {
    render(
      <MemoryRouter>
        <FileTree slug="audit-my-eval" stages={stages} approvedStages={[]} activeStage="01" gated={false} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /02_capability\.md/ })).toBeInTheDocument();
  });
});
