import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { StagePage } from "./StagePage";

const mockUseRun = vi.fn();
const mockUseSession = vi.fn();
vi.mock("../api/queries", () => ({
  useRun: (...args: unknown[]) => mockUseRun(...args),
  useSession: (...args: unknown[]) => mockUseSession(...args),
  useStageDiff: () => ({ data: undefined }),
  useRuns: () => ({ data: [] }),
  useRunFile: () => ({ data: undefined, isLoading: true, isError: false }),
  useRunTree: () => ({
    data: { tree: [{ name: "01_intended-use.md", path: "01_intended-use.md", is_dir: false, children: null }] },
    isLoading: false,
    isError: false,
  }),
}));

const mockStartStageMutateAsync = vi.fn();
vi.mock("../api/mutations", () => ({
  useStartStage: () => ({ mutateAsync: mockStartStageMutateAsync }),
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
  loadPanelCollapsed: vi.fn().mockReturnValue(null),
  storePanelCollapsed: vi.fn(),
}));

const runDetail = {
  slug: "design-my-eval",
  mode: "design",
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
  it("links back to the run list from the brand mark and offers a New run link", () => {
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /ecbd/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /new run/i })).toHaveAttribute("href", "/runs/new");
  });

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

  it("renders the file tree alongside the stage rail and document", () => {
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("navigation", { name: /stage progress/i })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: /run files/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /01_intended-use\.md/ })).toHaveAttribute(
      "href",
      "/runs/design-my-eval/stages/01",
    );
  });

  it("renders the chat panel with the panel variant class for a design run", () => {
    const { container } = render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(container.querySelector(".chat-drawer--panel")).toBeInTheDocument();
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

  it("picks up a newly-started chat session without needing an unrelated re-render", async () => {
    // loadSessionId is mocked to return null, so ChatDrawer starts in its
    // "no session yet" state and renders the start form. Driving that form
    // through startSession (-> useStartStage().mutateAsync, resolved here)
    // exercises ChatDrawer's real onSessionId callback, which StagePage
    // must be wired to for its own `sessionId` state to update.
    mockStartStageMutateAsync.mockResolvedValue({ session_id: "new-session-id" });
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/02"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    // Before starting a session, StagePage's useSession call is disabled
    // (sessionId is undefined).
    expect(mockUseSession.mock.calls.some(([arg]) => arg !== undefined)).toBe(false);

    await user.type(screen.getByPlaceholderText(/say what you need/i), "let's design an eval");
    await user.click(screen.getByRole("button", { name: /^start$/i }));

    expect(mockStartStageMutateAsync).toHaveBeenCalledWith("let's design an eval");

    // Once ChatDrawer's onSessionId fires, StagePage's own sessionId state
    // must update, which re-invokes useSession with a defined session id.
    expect(mockUseSession.mock.calls.some(([arg]) => arg === "new-session-id")).toBe(true);
  });

  it("hides chat, approve/reject, and stage locking for a non-design run", () => {
    mockUseRun.mockReturnValue({
      data: {
        ...runDetail,
        mode: "audit",
        approved_stages: [],
        stages: [
          { file: "01_sources.md", stage: "01", questions: "Framing", done: true },
          { file: "02_intended-use.md", stage: "02", questions: "Q1-2", done: false },
        ],
      },
      isLoading: false,
      isError: false,
    });

    const { container } = render(
      <MemoryRouter initialEntries={["/runs/audit-my-eval/stages/01"]}>
        <Routes>
          <Route path="/runs/:slug/stages/:stage" element={<StagePage />} />
        </Routes>
      </MemoryRouter>,
    );

    // No chat drawer: the backend's session/approve/reject endpoints are
    // hardcoded to the design pipeline's stage contracts.
    expect(screen.queryByRole("button", { name: /expand chat/i })).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/say what you need/i)).not.toBeInTheDocument();
    expect(container.querySelector(".chat-drawer--panel")).not.toBeInTheDocument();

    // Stage 02 isn't done and has no approved_stages to gate on, but an
    // audit run has no gate at all -- it must still be a live link, not a
    // locked, non-interactive item.
    expect(screen.getByRole("link", { name: /02/ })).toBeInTheDocument();
  });
});
