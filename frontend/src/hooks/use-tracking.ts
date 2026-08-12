import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface LinkMeta {
  needs_password: boolean;
  needs_consent: boolean;
}

export function useLinkMeta(code: string | undefined) {
  return useQuery({
    queryKey: ["tracking", "meta", code],
    queryFn: () => api.get<LinkMeta>(`/api/v1/t/${code}/meta`),
    enabled: !!code,
    retry: false,
  });
}

export function useResolveLink(code: string | undefined) {
  return useMutation({
    mutationFn: (body: { password?: string; consent: boolean }) =>
      api.post<{ target_url: string }>(`/api/v1/t/${code}/resolve`, body),
  });
}
