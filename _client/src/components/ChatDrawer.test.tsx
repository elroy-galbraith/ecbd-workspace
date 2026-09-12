import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ChatDrawer } from "./ChatDrawer";
import { ApiError } from "../api/client";

const mockLoadSessionId = vi.fn();
const mockStoreSessionId = vi.fn();
const mockClearSessionId = vi.fn();
const mockLoadPanelCollapsed = vi.fn();
const mockStorePanelCollapsed = vi.fn();
vi.mock("../lib/sessionStorage", () => ({
  loadSessionId: (...args: unknown[]) => mockLoadSessionId(...args),
  storeSessionId: (...args: unknown[]) => mockStoreSessionId(...args),
  clearSessionId: (...args: unknown[]) => mockClearSessionId(...args),
  loadPanelCollapsed: (...args: unknown[]) => mockLoadPanelCollapsed(...args),
  storePanelCollapsed: (...args: unknown[]) => mockStorePanelCollapsed(...args),
}));

const mockUseSession = vi.fn();
vi.mock("../api/queries", () => ({
  useSession: (...args: unknown[]) => mockUseSession(...args),
}));

const mockMutateAsync = vi.fn();
vi.mock("../api/mutations", () => ({
  useSendMessage: () => ({ mutateAsync: mockMutateAsync, isPending: false, isError: false, error: null }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockUseSession.mockReturnValue({ data: undefined, isError: false, error: null });
  mockLoadPanelCollapsed.mockReturnValue(null);
});

describe("ChatDrawer", () => {
  it("shows a start form when no session exists yet, and starts one", async () => {
    mockLoadSessionId.mockReturnValue(null);
    const startSession = vi.fn().mockResolvedValue({ session_id: "sess-1" });

    render(<ChatDrawer runKey="new" stage="01" startSession={startSession} />);

    await userEvent.type(screen.getByPlaceholderText(/say what you need/i), "I need a faithfulness eval");
    await userEvent.click(screen.getByRole("button", { name: /^start$/i }));

    expect(startSession).toHaveBeenCalledWith("I need a faithfulness eval");
    expect(mockStoreSessionId).toHaveBeenCalledWith("new", "01", "sess-1");
  });

  it("shows the transcript and a send form once a session exists", () => {
    mockLoadSessionId.mockReturnValue("sess-1");
    mockUseSession.mockReturnValue({
      data: { transcript: [{ role: "user", content: [{ type: "text", text: "hi" }] }], ready_for_review: false },
      isError: false,
      error: null,
    });

    render(<ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} />);
    userEvent.click(screen.getByRole("button", { name: /expand chat/i }));
  });

  it("offers to start over when the stored session is gone (404)", () => {
    mockLoadSessionId.mockReturnValue("sess-stale");
    mockUseSession.mockReturnValue({ data: undefined, isError: true, error: new ApiError(404, "no such session") });

    render(<ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/no longer available/i);
  });

  it("defaults to collapsed when nothing is stored (matching today's behavior), and persists an expand", async () => {
    mockLoadSessionId.mockReturnValue("sess-1");
    mockUseSession.mockReturnValue({
      data: { transcript: [], ready_for_review: false },
      isError: false,
      error: null,
    });

    render(<ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} variant="panel" />);

    expect(screen.getByRole("button", { name: /expand chat/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /expand chat/i }));
    expect(mockStorePanelCollapsed).toHaveBeenCalledWith("design-my-eval", "chat", false);
  });

  it("restores a previously-expanded panel from storage", () => {
    mockLoadSessionId.mockReturnValue("sess-1");
    mockLoadPanelCollapsed.mockReturnValue(false);
    mockUseSession.mockReturnValue({
      data: { transcript: [], ready_for_review: false },
      isError: false,
      error: null,
    });

    render(<ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} variant="panel" />);

    expect(screen.getByRole("button", { name: /collapse chat/i })).toBeInTheDocument();
  });

  it("applies the panel variant class when requested, and the drawer variant by default", () => {
    mockLoadSessionId.mockReturnValue(null);
    const { container: panelContainer } = render(
      <ChatDrawer runKey="design-my-eval" stage="02" startSession={vi.fn()} variant="panel" />,
    );
    expect(panelContainer.querySelector(".chat-drawer--panel")).toBeInTheDocument();

    const { container: drawerContainer } = render(
      <ChatDrawer runKey="new" stage="01" startSession={vi.fn()} />,
    );
    expect(drawerContainer.querySelector(".chat-drawer--drawer")).toBeInTheDocument();
  });
});
