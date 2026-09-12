import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useRuns, useRunTree } from "./queries";

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("useRuns", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches the run list from /runs", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ slug: "design-my-eval", mode: "design", subject: "s", opened: "2026-09-09" }],
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useRuns(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([
      { slug: "design-my-eval", mode: "design", subject: "s", opened: "2026-09-09" },
    ]);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/runs"), expect.anything());
  });
});

describe("useRunTree", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches a run's file tree from /runs/:slug/tree", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        tree: [{ name: "RUN.md", path: "RUN.md", is_dir: false, children: null }],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useRunTree("design-my-eval"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({
      tree: [{ name: "RUN.md", path: "RUN.md", is_dir: false, children: null }],
    });
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/runs/design-my-eval/tree"), expect.anything());
  });
});
