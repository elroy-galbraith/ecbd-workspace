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
vi.mock("../lib/sessionStorage", () => ({
  storeSessionId: (...args: unknown[]) => mockStoreSessionId(...args),
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
    expect(await screen.findByText(/landed on the new run's stage page/i)).toBeInTheDocument();
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
});
