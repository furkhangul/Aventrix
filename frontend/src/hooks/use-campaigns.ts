import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Campaign, CampaignStatus, Paginated } from "@/lib/types";

interface CampaignListParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: CampaignStatus;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function useCampaigns(params: CampaignListParams = {}) {
  const { page = 1, pageSize = 20, search, status } = params;
  return useQuery({
    queryKey: ["campaigns", page, pageSize, search, status],
    queryFn: () =>
      api.get<Paginated<Campaign>>(
        `/api/v1/campaigns${buildQuery({ page, page_size: pageSize, search, status_filter: status })}`,
      ),
    placeholderData: (prev) => prev,
  });
}

export function useCampaign(id: string | undefined) {
  return useQuery({
    queryKey: ["campaigns", id],
    queryFn: () => api.get<Campaign>(`/api/v1/campaigns/${id}`),
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; description?: string; tags?: string[] }) =>
      api.post<Campaign>("/api/v1/campaigns", body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["campaigns"] }),
  });
}

export function useUpdateCampaign(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { name?: string; description?: string; tags?: string[]; status?: CampaignStatus }) =>
      api.patch<Campaign>(`/api/v1/campaigns/${id}`, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["campaigns"] }),
  });
}

export function useDeleteCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/campaigns/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["campaigns"] }),
  });
}
