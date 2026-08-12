import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiKey, ApiKeyCreated, ApiKeyTier, Paginated } from "@/lib/types";

export function useApiKeys(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["api-keys", page, pageSize],
    queryFn: () => api.get<Paginated<ApiKey>>(`/api/v1/api-keys?page=${page}&page_size=${pageSize}`),
    placeholderData: (prev) => prev,
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; tier: ApiKeyTier }) => api.post<ApiKeyCreated>("/api/v1/api-keys", body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });
}

export function useRotateApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post<ApiKeyCreated>(`/api/v1/api-keys/${id}/rotate`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/api-keys/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });
}
