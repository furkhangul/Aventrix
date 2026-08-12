import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Paginated, Webhook, WebhookCreated, WebhookDelivery, WebhookEventType } from "@/lib/types";

export function useWebhooks(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["webhooks", page, pageSize],
    queryFn: () => api.get<Paginated<Webhook>>(`/api/v1/webhooks?page=${page}&page_size=${pageSize}`),
    placeholderData: (prev) => prev,
  });
}

export function useWebhookDeliveries(webhookId: string | undefined, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["webhooks", webhookId, "deliveries", page, pageSize],
    queryFn: () =>
      api.get<Paginated<WebhookDelivery>>(
        `/api/v1/webhooks/${webhookId}/deliveries?page=${page}&page_size=${pageSize}`,
      ),
    enabled: !!webhookId,
    refetchInterval: 5000,
  });
}

export interface WebhookInput {
  url: string;
  description?: string;
  events: WebhookEventType[];
}

export function useCreateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: WebhookInput) => api.post<WebhookCreated>("/api/v1/webhooks", body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["webhooks"] }),
  });
}

export function useUpdateWebhook(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<WebhookInput & { is_active: boolean }>) =>
      api.patch<Webhook>(`/api/v1/webhooks/${id}`, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["webhooks"] }),
  });
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/webhooks/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["webhooks"] }),
  });
}

export function useTestWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post<WebhookDelivery>(`/api/v1/webhooks/${id}/test`),
    onSuccess: (_data, id) => queryClient.invalidateQueries({ queryKey: ["webhooks", id, "deliveries"] }),
  });
}
