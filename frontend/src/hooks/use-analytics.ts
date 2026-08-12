import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AnalyticsOverview, DateRangePreset } from "@/lib/types";

interface AnalyticsParams {
  range: DateRangePreset;
  linkId?: string;
  campaignId?: string;
}

function buildQuery(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) search.set(key, value);
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function useAnalyticsOverview({ range, linkId, campaignId }: AnalyticsParams) {
  return useQuery({
    queryKey: ["analytics", "overview", range, linkId, campaignId],
    queryFn: () =>
      api.get<AnalyticsOverview>(
        `/api/v1/analytics/overview${buildQuery({ range, link_id: linkId, campaign_id: campaignId })}`,
      ),
  });
}

export function buildAnalyticsExportUrl({
  range,
  linkId,
  campaignId,
  format,
}: AnalyticsParams & { format: "csv" | "json" }): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  return `${base}/api/v1/analytics/export${buildQuery({ range, link_id: linkId, campaign_id: campaignId, format })}`;
}
