import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { StagePage } from "./StagePage";

const mockUseRun = vi.fn();
const mockUseSession = vi.fn();
vi.mock("../api/queries", () => ({
  useRun: (...args: unknown[]) => mockUseRun(...args),
  useSession: (...args: unknown[]) => mockUseSession(...args),
  useStageDiff: () => ({ data: undefined }),
  useRuns: () => ({ data: [] }),
  useRunFile: () => ({ data: undefined, isLoading: true, isError: false }),
}));

vi.mock("../api/mutations", () => ({
  useStartStage: () => ({ mutateAsync: vi.fn() }),
  useApproveStage: () => ({ mutate: vi.fn(), isPending: false }),
  useRejectStage: () => ({ mutate: vi.fn() }),
  useSaveFile: () => ({ mutate: vi.fn(), isPending: false }),
  // StagePage renders the real ChatDrawer (not mocked), which calls
  // useSendMessage -- must be provided here too or that call throws.
  useSendMessage: () => ({ mutateAsync: vi.fn(), isPending: false, isError: false, error: null }),
}));

vi.mock("../lib/sessionStorage", () => ({
  loadSessionId: () => null,
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
    { file: "01_intended-use.md", stage: "01", questions: "Q1-2", done: true },
    { file: "02_capability.md", stage: "02", questions: "Q3-5", done: false },
  ],
  loop_backs: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  mockUseRun.mockReturnValue({ data: runDetail, isLoading: false, isError: false });
  mockUseSession.mockReturnValue({ data: undefined, isError: false, error: null });
});

describe("StagePage", () => {
  it("renders the stage rail and the current stage's document, but no review banner when not ready", () => {
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("navigation", { name: /stage progress/i })).toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("shows the review banner once the session reports ready_for_review", () => {
    mockUseSession.mockReturnValue({
      data: { transcript: [], ready_for_review: true },
      isError: false,
      error: null,
    });

    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows an error state when the run fails to load", () => {
    mockUseRun.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
