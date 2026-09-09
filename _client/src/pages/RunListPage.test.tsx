import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { RunListPage } from "./RunListPage";

const mockUseRuns = vi.fn();
vi.mock("../api/queries", () => ({
  useRuns: () => mockUseRuns(),
}));

describe("RunListPage", () => {
  it("lists runs with a link to each, and a New run link", () => {
    mockUseRuns.mockReturnValue({
      data: [{ slug: "design-my-eval", mode: "design", subject: "Faithfulness", opened: "2026-09-09" }],
      isLoading: false,
      isError: false,
    });

    render(
      <MemoryRouter>
        <RunListPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "design-my-eval" })).toHaveAttribute(
      "href",
      "/runs/design-my-eval",
    );
    expect(screen.getByRole("link", { name: /new run/i })).toHaveAttribute("href", "/runs/new");
  });

  it("shows an error state when the run list fails to load", () => {
    mockUseRuns.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    render(
      <MemoryRouter>
        <RunListPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
