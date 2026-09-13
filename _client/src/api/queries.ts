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

export function useSession(sessionId: string | undefined, slug?: string, stage?: string) {
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
