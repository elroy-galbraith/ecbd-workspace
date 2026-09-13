import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { DiffResponse, FileContent, RunDetail, RunSummary, RunTree, SessionState } from "./types";

export function useRuns() {
  return useQuery({ queryKey: ["runs"], queryFn: () => api.get<RunSummary[]>("/runs") });
}

export function useRun(slug: string | undefined) {
  return useQuery({
    queryKey: ["run", slug],
    queryFn: () => api.get<RunDetail>(`/runs/${slug}`),
    enabled: slug !== undefined,
  });
}

export function useSession(
  sessionId: string | undefined,
  slug?: string,
  stage?: string,
  options?: { live?: boolean },
) {
  return useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => {
      // slug/stage let the backend rehydrate a session it lost track of
      // (e.g. after a restart) that predates its own metadata sidecar.
      const query = slug && stage ? `?${new URLSearchParams({ slug, stage })}` : "";
      return api.get<SessionState>(`/sessions/${sessionId}${query}`);
    },
    enabled: sessionId !== undefined,
    retry: false,
    // While a reply is in flight, the backend appends each tool call to the
    // session's transcript as it happens -- polling surfaces that live
    // instead of only showing the final result once the request completes.
    refetchInterval: options?.live ? 1000 : undefined,
  });
}

export function useRunFile(slug: string | undefined, path: string | undefined) {
  return useQuery({
    queryKey: ["file", slug, path],
    queryFn: () => api.get<FileContent>(`/runs/${slug}/files/${path}`),
    enabled: slug !== undefined && path !== undefined,
  });
}

export function useRunTree(slug: string | undefined) {
  return useQuery({
    queryKey: ["tree", slug],
    queryFn: () => api.get<RunTree>(`/runs/${slug}/tree`),
    enabled: slug !== undefined,
  });
}

export function useStageDiff(slug: string | undefined, stage: string | undefined) {
  return useQuery({
    queryKey: ["diff", slug, stage],
    queryFn: () => api.get<DiffResponse>(`/runs/${slug}/diff/${stage}`),
    enabled: slug !== undefined && stage !== undefined,
  });
}
