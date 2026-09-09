import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { App } from "./App";

const mockUseRun = vi.fn();
vi.mock("./api/queries", () => ({
  useRun: (...args: unknown[]) => mockUseRun(...args),
  useSession: () => ({ data: undefined, isError: false, error: null }),
  useStageDiff: () => ({ data: undefined }),
  useRuns: () => ({ data: [] }),
  useRunFile: () => ({ data: undefined, isLoading: true, isError: false }),
}));

vi.mock("./api/mutations", () => ({
  useStartStage: () => ({ mutateAsync: vi.fn() }),
  useApproveStage: () => ({ mutate: vi.fn(), isPending: false }),
  useRejectStage: () => ({ mutate: vi.fn() }),
  useSaveFile: () => ({ mutate: vi.fn(), isPending: false }),
  useSendMessage: () => ({ mutateAsync: vi.fn(), isPending: false, isError: false, error: null }),
}));

const mockLoadSessionId = vi.fn();
vi.mock("./lib/sessionStorage", () => ({
  loadSessionId: (...args: unknown[]) => mockLoadSessionId(...args),
  storeSessionId: vi.fn(),
  clearSessionId: vi.fn(),
}));

const runDetail = {
  slug: "design-my-eval",
  status: "in-progress",
  opened: "2026-09-09",
  closed: null,
  approved_stages: ["01"],
  stages: [
    { file: "01_intended-use.md", stage: "01", questions: "", done: true },
    { file: "02_capability.md", stage: "02", questions: "", done: false },
  ],
  loop_backs: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  mockUseRun.mockReturnValue({ data: runDetail, isLoading: false, isError: false });
});

describe("stage navigation remounts StagePage", () => {
  it("does not carry ChatDrawer's active-session state from one stage to the next", async () => {
    mockLoadSessionId.mockImplementation((_runKey: string, stage: string) =>
      stage === "01" ? "session-from-stage-01" : null,
    );
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/01"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: /expand chat/i })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /^02$/ }));

    expect(screen.getByRole("button", { name: /^start$/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /expand chat/i })).not.toBeInTheDocument();
  });
});
