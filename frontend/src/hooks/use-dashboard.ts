import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { DashboardSummary, DateRangePreset, TimeseriesPoint, TopItem } from "@/lib/types";

export function useDashboardSummary(range: DateRangePreset) {
  return useQuery({
    queryKey: ["dashboard", "summary", range],
    queryFn: () => api.get<DashboardSummary>(`/api/v1/dashboard/summary?range=${range}`),
  });
}

export function useDashboardTimeseries(range: DateRangePreset) {
  return useQuery({
    queryKey: ["dashboard", "timeseries", range],
    queryFn: () => api.get<TimeseriesPoint[]>(`/api/v1/dashboard/timeseries?range=${range}`),
  });
}

export function useDashboardTop(dimension: "country" | "device" | "browser" | "referrer" | "os", range: DateRangePreset) {
  return useQuery({
    queryKey: ["dashboard", "top", dimension, range],
    queryFn: () => api.get<TopItem[]>(`/api/v1/dashboard/top/${dimension}?range=${range}`),
  });
}
