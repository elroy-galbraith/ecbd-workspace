import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { RunSwitcher } from "./RunSwitcher";

vi.mock("../api/queries", () => ({
  useRuns: () => ({
    data: [
      { slug: "design-my-eval", mode: "design", subject: "Faithfulness", opened: "2026-09-09" },
      { slug: "design-other", mode: "design", subject: "Other run", opened: "2026-09-08" },
    ],
  }),
}));

function LocationProbe() {
  return null;
}

describe("RunSwitcher", () => {
  it("lists every run and navigates on selection", async () => {
    render(
      <MemoryRouter initialEntries={["/runs/design-my-eval/stages/01"]}>
        <RunSwitcher currentSlug="design-my-eval" />
        <Routes>
          <Route path="/runs/:slug" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    const select = screen.getByRole("combobox", { name: /switch run/i });
    expect(select).toHaveValue("design-my-eval");
    expect(screen.getByRole("option", { name: /other run/i })).toBeInTheDocument();

    await userEvent.selectOptions(select, "design-other");
    expect(select).toHaveValue("design-other");
  });
});
