import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { DiffResponse, FileContent, RunDetail, RunSummary, SessionState } from "./types";

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

export function useSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => api.get<SessionState>(`/sessions/${sessionId}`),
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

export function useStageDiff(slug: string | undefined, stage: string | undefined) {
  return useQuery({
    queryKey: ["diff", slug, stage],
    queryFn: () => api.get<DiffResponse>(`/runs/${slug}/diff/${stage}`),
    enabled: slug !== undefined && stage !== undefined,
  });
}
