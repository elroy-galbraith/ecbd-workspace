import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RejectDialog } from "./RejectDialog";

describe("RejectDialog", () => {
  it("submits the chosen target stage and typed reason, excluding the current stage from choices", async () => {
    const onSubmit = vi.fn();
    render(
      <RejectDialog
        approvedStages={["01", "02"]}
        currentStage="02"
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.queryByRole("option", { name: "02" })).not.toBeInTheDocument();
    expect(screen.getByRole("option", { name: "01" })).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/reason/i), "intended use was too vague");
    await userEvent.click(screen.getByRole("button", { name: /^reject$/i }));

    expect(onSubmit).toHaveBeenCalledWith({ target_stage: "01", reason: "intended use was too vague" });
  });

  it("disables Reject until a reason is typed", () => {
    render(
      <RejectDialog approvedStages={["01"]} currentStage="02" onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: /^reject$/i })).toBeDisabled();
  });

  it("calls onCancel when Cancel is clicked", async () => {
    const onCancel = vi.fn();
    render(
      <RejectDialog approvedStages={["01"]} currentStage="02" onSubmit={vi.fn()} onCancel={onCancel} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
