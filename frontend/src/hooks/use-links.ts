import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Link, Paginated, UtmParams, Visit } from "@/lib/types";

interface LinkListParams {
  page?: number;
  pageSize?: number;
  search?: string;
  campaignId?: string;
  isActive?: boolean;
}

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function useLinks(params: LinkListParams = {}) {
  const { page = 1, pageSize = 20, search, campaignId, isActive } = params;
  return useQuery({
    queryKey: ["links", page, pageSize, search, campaignId, isActive],
    queryFn: () =>
      api.get<Paginated<Link>>(
        `/api/v1/links${buildQuery({ page, page_size: pageSize, search, campaign_id: campaignId, is_active: isActive })}`,
      ),
    placeholderData: (prev) => prev,
  });
}

export function useLink(id: string | undefined) {
  return useQuery({
    queryKey: ["links", id],
    queryFn: () => api.get<Link>(`/api/v1/links/${id}`),
    enabled: !!id,
  });
}

export function useLinkVisits(linkId: string, page: number, pageSize = 10, enabled = true) {
  return useQuery({
    queryKey: ["links", linkId, "visits", page, pageSize],
    queryFn: () => api.get<Paginated<Visit>>(`/api/v1/links/${linkId}/visits?page=${page}&page_size=${pageSize}`),
    enabled: enabled && !!linkId,
    placeholderData: (prev) => prev,
  });
}

export interface CreateLinkInput {
  target_url: string;
  campaign_id?: string;
  custom_alias?: string;
  description?: string;
  tags?: string[];
  expires_at?: string;
  password?: string;
  requires_consent: boolean;
  utm: UtmParams;
}

export function useCreateLink() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateLinkInput) => api.post<Link>("/api/v1/links", body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["links"] });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}

export function useUpdateLink(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<{ target_url: string; description: string; tags: string[]; expires_at: string | null; is_active: boolean; requires_consent: boolean; campaign_id: string }>) =>
      api.patch<Link>(`/api/v1/links/${id}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["links"] });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}

export function useSetLinkPassword(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (password: string | null) => api.put<Link>(`/api/v1/links/${id}/password`, { password }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["links"] }),
  });
}

export function useDeleteLink() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/links/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["links"] });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}
