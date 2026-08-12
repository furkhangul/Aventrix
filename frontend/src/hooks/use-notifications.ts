import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { NotificationList } from "@/lib/types";

export function useNotifications(params: { page?: number; pageSize?: number; unreadOnly?: boolean } = {}) {
  const { page = 1, pageSize = 20, unreadOnly = false } = params;
  return useQuery({
    queryKey: ["notifications", page, pageSize, unreadOnly],
    queryFn: () =>
      api.get<NotificationList>(
        `/api/v1/notifications?page=${page}&page_size=${pageSize}&unread_only=${unreadOnly}`,
      ),
    placeholderData: (prev) => prev,
  });
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => api.get<NotificationList>("/api/v1/notifications?page=1&page_size=5"),
    refetchInterval: 30_000,
    select: (data) => ({ count: data.unread_count, recent: data.items }),
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.patch(`/api/v1/notifications/${id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/api/v1/notifications/read-all"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/notifications/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: ["notifications", "preferences"],
    queryFn: () => api.get<{ preferences: Record<string, boolean> }>("/api/v1/notifications/preferences"),
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (preferences: Record<string, boolean>) =>
      api.patch<{ preferences: Record<string, boolean> }>("/api/v1/notifications/preferences", { preferences }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications", "preferences"] }),
  });
}
