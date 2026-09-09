import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { DocumentPane } from "./DocumentPane";

const mockUseRunFile = vi.fn();
vi.mock("../api/queries", () => ({
  useRunFile: (...args: unknown[]) => mockUseRunFile(...args),
}));

const mockMutate = vi.fn();
vi.mock("../api/mutations", () => ({
  useSaveFile: () => ({ mutate: mockMutate, isPending: false }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("DocumentPane", () => {
  it("shows a folder notice instead of a textarea for a directory output", () => {
    mockUseRunFile.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });
    render(<DocumentPane slug="design-my-eval" file="build/" />);
    expect(screen.getByText(/no single-file viewer yet/i)).toBeInTheDocument();
  });

  it("loads content into an editable textarea and enables Save once edited", async () => {
    mockUseRunFile.mockReturnValue({
      data: { path: "01_intended-use.md", content: "original text" },
      isLoading: false,
      isError: false,
    });

    render(<DocumentPane slug="design-my-eval" file="01_intended-use.md" />);
    const textarea = screen.getByDisplayValue("original text");
    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();

    await userEvent.type(textarea, " and more");
    expect(screen.getByRole("button", { name: /save/i })).toBeEnabled();

    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(mockMutate).toHaveBeenCalledWith("original text and more", expect.anything());
  });

  it("shows an error state when the file fails to load", () => {
    mockUseRunFile.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    render(<DocumentPane slug="design-my-eval" file="01_intended-use.md" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
