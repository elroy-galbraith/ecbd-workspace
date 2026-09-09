import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("renders the workspace name", () => {
    render(<App />);
    expect(screen.getByText(/ecbd-workspace/i)).toBeInTheDocument();
  });
});
