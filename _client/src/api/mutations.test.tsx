import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useSendMessage } from "./mutations";

describe("useSendMessage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("invalidates both the session and the run's file queries on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ reply: "ok" }) }),
    );

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    function wrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    }

    const { result } = renderHook(() => useSendMessage("session-1", "design-my-eval"), { wrapper });

    await result.current.mutateAsync("hello");

    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["session", "session-1"] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["file", "design-my-eval"] });
    });
  });

  it("does not attempt a file invalidation when no slug is given", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ reply: "ok" }) }),
    );

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    function wrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    }

    const { result } = renderHook(() => useSendMessage("session-1"), { wrapper });

    await result.current.mutateAsync("hello");

    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["session", "session-1"] });
    });
    expect(invalidateSpy).not.toHaveBeenCalledWith({ queryKey: ["file", "design-my-eval"] });
  });
});
