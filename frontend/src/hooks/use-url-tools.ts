import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { RedirectCheckResult, UrlAnalysisResult } from "@/lib/types";

export function useAnalyzeUrl() {
  return useMutation({
    mutationFn: (url: string) => api.post<UrlAnalysisResult>("/api/v1/url-tools/analyze", { url }),
  });
}

export function useRedirectCheck() {
  return useMutation({
    mutationFn: (url: string) => api.post<RedirectCheckResult>("/api/v1/url-tools/redirect-check", { url }),
  });
}
