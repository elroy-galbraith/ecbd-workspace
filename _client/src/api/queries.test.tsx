import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useRuns, useRunTree, useSession } from "./queries";

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

describe("useSession", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("polls every second when live is true", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ transcript: [], ready_for_review: false }),
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.useFakeTimers();

    renderHook(() => useSession("sess-1", undefined, undefined, { live: true }), { wrapper });
    await vi.advanceTimersByTimeAsync(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(1000);
    expect(fetchMock).toHaveBeenCalledTimes(2);

    await vi.advanceTimersByTimeAsync(1000);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("does not poll when live is false or omitted", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ transcript: [], ready_for_review: false }),
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.useFakeTimers();

    renderHook(() => useSession("sess-1"), { wrapper });
    await vi.advanceTimersByTimeAsync(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(5000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
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
