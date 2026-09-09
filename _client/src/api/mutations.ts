import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { ApproveResponse, FileContent } from "./types";

export function useStartRun() {
  return useMutation({
    mutationFn: (brief: string) => api.post<{ session_id: string }>("/runs/design/start", { brief }),
  });
}

export function useStartStage(slug: string, stage: string) {
  return useMutation({
    mutationFn: (brief: string) =>
      api.post<{ session_id: string }>(`/runs/${slug}/stages/${stage}/start`, { brief }),
  });
}

export function useSendMessage(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (brief: string) => api.post<{ reply: string }>(`/sessions/${sessionId}/messages`, { brief }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
    },
  });
}

export function useApproveStage(slug: string, stage: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<ApproveResponse>(`/runs/${slug}/stages/${stage}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", slug] });
    },
  });
}

export function useRejectStage(slug: string, stage: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { target_stage: string; reason: string }) =>
      api.post<{ status: string }>(`/runs/${slug}/stages/${stage}/reject`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", slug] });
    },
  });
}

export function useSaveFile(slug: string, path: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => api.put<FileContent>(`/runs/${slug}/files/${path}`, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["file", slug, path] });
    },
  });
}
