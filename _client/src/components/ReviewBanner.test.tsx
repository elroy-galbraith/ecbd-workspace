import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ReviewBanner } from "./ReviewBanner";

describe("ReviewBanner", () => {
  it("calls the right handler for each action", async () => {
    const onViewDiff = vi.fn();
    const onApprove = vi.fn();
    const onReject = vi.fn();
    render(<ReviewBanner onViewDiff={onViewDiff} onApprove={onApprove} onReject={onReject} approving={false} />);

    await userEvent.click(screen.getByRole("button", { name: /view diff/i }));
    await userEvent.click(screen.getByRole("button", { name: /^approve$/i }));
    await userEvent.click(screen.getByRole("button", { name: /reject/i }));

    expect(onViewDiff).toHaveBeenCalledOnce();
    expect(onApprove).toHaveBeenCalledOnce();
    expect(onReject).toHaveBeenCalledOnce();
  });

  it("disables Approve and shows progress while approving", () => {
    render(<ReviewBanner onViewDiff={vi.fn()} onApprove={vi.fn()} onReject={vi.fn()} approving={true} />);
    expect(screen.getByRole("button", { name: /approving/i })).toBeDisabled();
  });
});
