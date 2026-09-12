import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { StageRail, isStageUnlocked } from "./StageRail";
import type { StageTableRow } from "../api/types";

const stages: StageTableRow[] = [
  { file: "01_intended-use.md", stage: "01", questions: "Q1-2", done: true },
  { file: "02_capability.md", stage: "02", questions: "Q3-5", done: false },
  { file: "03_content.md", stage: "03", questions: "Q6-8", done: false },
];

describe("isStageUnlocked", () => {
  it("the first stage is always unlocked", () => {
    expect(isStageUnlocked(stages, [], "01")).toBe(true);
  });

  it("a later stage is locked until every prior stage is approved", () => {
    expect(isStageUnlocked(stages, [], "02")).toBe(false);
    expect(isStageUnlocked(stages, ["01"], "02")).toBe(true);
  });

  it("stage 3 needs both 1 and 2 approved", () => {
    expect(isStageUnlocked(stages, ["01"], "03")).toBe(false);
    expect(isStageUnlocked(stages, ["01", "02"], "03")).toBe(true);
  });
});

describe("StageRail", () => {
  it("renders locked stages as non-links and unlocked stages as links", () => {
    render(
      <MemoryRouter>
        <StageRail slug="design-my-eval" stages={stages} approvedStages={["01"]} activeStage="02" />
      </MemoryRouter>,
    );

    const stage01 = screen.getByRole("link", { name: /01/ });
    expect(stage01).toHaveAttribute("href", "/runs/design-my-eval/stages/01");

    const stage03 = screen.getByText(/03/);
    expect(stage03).toHaveAttribute("aria-disabled", "true");
    expect(screen.queryByRole("link", { name: /03/ })).not.toBeInTheDocument();
  });

  it("ungated (audit/measure) runs render every stage as a link, done or not", () => {
    render(
      <MemoryRouter>
        <StageRail slug="audit-my-eval" stages={stages} approvedStages={[]} activeStage="01" gated={false} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /02/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /03/ })).toBeInTheDocument();
  });
});
