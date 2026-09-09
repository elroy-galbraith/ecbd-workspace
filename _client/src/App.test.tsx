import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { App } from "./App";

vi.mock("./pages/RunListPage", () => ({ RunListPage: () => <div>run-list-page</div> }));
vi.mock("./pages/NewRunPage", () => ({ NewRunPage: () => <div>new-run-page</div> }));
vi.mock("./pages/StagePage", () => ({ StagePage: () => <div>stage-page</div> }));

const mockUseRun = vi.fn();
vi.mock("./api/queries", () => ({
  useRun: (...args: unknown[]) => mockUseRun(...args),
}));

function renderApp(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <App />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("App routing", () => {
  it("renders the run list at /", () => {
    renderApp("/");
    expect(screen.getByText("run-list-page")).toBeInTheDocument();
  });

  it("renders the new-run page at /runs/new", () => {
    renderApp("/runs/new");
    expect(screen.getByText("new-run-page")).toBeInTheDocument();
  });

  it("renders the stage page directly at /runs/:slug/stages/:stage", () => {
    renderApp("/runs/design-my-eval/stages/02");
    expect(screen.getByText("stage-page")).toBeInTheDocument();
  });

  it("redirects /runs/:slug to the run's current (first non-approved) stage", () => {
    mockUseRun.mockReturnValue({
      data: {
        slug: "design-my-eval",
        approved_stages: ["01"],
        stages: [
          { file: "01_intended-use.md", stage: "01", questions: "", done: true },
          { file: "02_capability.md", stage: "02", questions: "", done: false },
        ],
      },
      isLoading: false,
      isError: false,
    });
    renderApp("/runs/design-my-eval");
    expect(screen.getByText("stage-page")).toBeInTheDocument();
  });
});
