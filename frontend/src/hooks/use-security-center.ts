import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Paginated, SecurityScan } from "@/lib/types";

export function useSecurityScans(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["security-scans", page, pageSize],
    queryFn: () => api.get<Paginated<SecurityScan>>(`/api/v1/security-center/scans?page=${page}&page_size=${pageSize}`),
    placeholderData: (prev) => prev,
  });
}

export function useSecurityScan(id: string | undefined) {
  return useQuery({
    queryKey: ["security-scans", id],
    queryFn: () => api.get<SecurityScan>(`/api/v1/security-center/scans/${id}`),
    enabled: !!id,
  });
}

export function useRunSecurityScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (domain: string) => api.post<SecurityScan>("/api/v1/security-center/scan", { domain }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["security-scans"] }),
  });
}
