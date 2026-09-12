import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { NewRunPage } from "./NewRunPage";

const mockUseRuns = vi.fn();
vi.mock("../api/queries", () => ({
  useRuns: () => mockUseRuns(),
}));

const mockMutateAsync = vi.fn();
vi.mock("../api/mutations", () => ({
  useStartRun: () => ({ mutateAsync: mockMutateAsync }),
}));

const mockApiGet = vi.fn();
vi.mock("../api/client", () => ({
  api: { get: (...args: unknown[]) => mockApiGet(...args) },
}));

const mockStoreSessionId = vi.fn();
const mockClearSessionId = vi.fn();
vi.mock("../lib/sessionStorage", () => ({
  storeSessionId: (...args: unknown[]) => mockStoreSessionId(...args),
  clearSessionId: (...args: unknown[]) => mockClearSessionId(...args),
}));

vi.mock("../components/ChatDrawer", () => ({
  ChatDrawer: ({ onSessionId }: { onSessionId?: (id: string) => void }) => (
    <button onClick={() => onSessionId?.("sess-new")}>simulate session start</button>
  ),
}));

function LandingProbe() {
  return <p>landed on the new run's stage page</p>;
}

beforeEach(() => {
  vi.clearAllMocks();
  mockUseRuns.mockReturnValue({ data: [] });
});

describe("NewRunPage", () => {
  it("links back to the run list from the brand mark and the Runs button", () => {
    render(
      <MemoryRouter initialEntries={["/runs/new"]}>
        <Routes>
          <Route path="/runs/new" element={<NewRunPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /ecbd/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /^runs$/i })).toHaveAttribute("href", "/");
  });

  it("offers Check for created run only after a session has started, and navigates once a new slug appears", async () => {
    render(
      <MemoryRouter initialEntries={["/runs/new"]}>
        <Routes>
          <Route path="/runs/new" element={<NewRunPage />} />
          <Route path="/runs/:slug/stages/:stage" element={<LandingProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.queryByRole("button", { name: /check for created run/i })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /simulate session start/i }));
    expect(screen.getByRole("button", { name: /check for created run/i })).toBeInTheDocument();

    mockApiGet.mockResolvedValue([{ slug: "design-my-eval", mode: "design", subject: "s", opened: "2026-09-09" }]);
    await userEvent.click(screen.getByRole("button", { name: /check for created run/i }));

    expect(mockStoreSessionId).toHaveBeenCalledWith("design-my-eval", "01", "sess-new");
    expect(mockClearSessionId).toHaveBeenCalledWith("new", "01");
    expect(await screen.findByText(/landed on the new run's stage page/i)).toBeInTheDocument();
  });

  it("finds a newly created run and navigates automatically, with no click needed", async () => {
    // Regression test: relying on the user to remember "Check for created
    // run" before navigating away was the actual root cause of losing the
    // session_id<->run link entirely (see StagePage.test.tsx's durable-tick
    // fallback test) -- this must work passively in the background.
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      render(
        <MemoryRouter initialEntries={["/runs/new"]}>
          <Routes>
            <Route path="/runs/new" element={<NewRunPage />} />
            <Route path="/runs/:slug/stages/:stage" element={<LandingProbe />} />
          </Routes>
        </MemoryRouter>,
      );

      await userEvent.click(screen.getByRole("button", { name: /simulate session start/i }));
      mockApiGet.mockResolvedValue([{ slug: "design-my-eval", mode: "design", subject: "s", opened: "2026-09-09" }]);

      await vi.advanceTimersByTimeAsync(4000);

      expect(mockStoreSessionId).toHaveBeenCalledWith("design-my-eval", "01", "sess-new");
      expect(mockClearSessionId).toHaveBeenCalledWith("new", "01");
      expect(await screen.findByText(/landed on the new run's stage page/i)).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("stays quiet in the background while no run has appeared yet -- no alert spam", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      render(
        <MemoryRouter initialEntries={["/runs/new"]}>
          <Routes>
            <Route path="/runs/new" element={<NewRunPage />} />
          </Routes>
        </MemoryRouter>,
      );

      await userEvent.click(screen.getByRole("button", { name: /simulate session start/i }));
      mockApiGet.mockResolvedValue([]);

      await vi.advanceTimersByTimeAsync(4000);

      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("reports when no new run has appeared yet", async () => {
    render(
      <MemoryRouter initialEntries={["/runs/new"]}>
        <Routes>
          <Route path="/runs/new" element={<NewRunPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByRole("button", { name: /simulate session start/i }));
    mockApiGet.mockResolvedValue([]);
    await userEvent.click(screen.getByRole("button", { name: /check for created run/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/no new run yet/i);
  });

  it("shows an error banner when the check itself fails", async () => {
    render(
      <MemoryRouter initialEntries={["/runs/new"]}>
        <Routes>
          <Route path="/runs/new" element={<NewRunPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByRole("button", { name: /simulate session start/i }));
    mockApiGet.mockRejectedValue(new Error("network down"));
    await userEvent.click(screen.getByRole("button", { name: /check for created run/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/network down/i);
  });
});
