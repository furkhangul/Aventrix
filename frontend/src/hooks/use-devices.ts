import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Device,
  DeviceSession,
  DeviceSessionStart,
  Paginated,
  PairingCodeCreated,
} from "@/lib/types";

export function useDevices(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["devices", page, pageSize],
    queryFn: () => api.get<Paginated<Device>>(`/api/v1/devices?page=${page}&page_size=${pageSize}`),
    placeholderData: (prev) => prev,
  });
}

export function useDeviceSessions(deviceId: string | undefined, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["devices", deviceId, "sessions", page, pageSize],
    queryFn: () =>
      api.get<Paginated<DeviceSession>>(
        `/api/v1/devices/${deviceId}/sessions?page=${page}&page_size=${pageSize}`,
      ),
    enabled: !!deviceId,
  });
}

export function useCreatePairingCode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<PairingCodeCreated>("/api/v1/devices/pairing-codes"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices"] }),
  });
}

export function useRenameDevice(deviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.patch<Device>(`/api/v1/devices/${deviceId}`, { name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices"] }),
  });
}

export function useRevokeDevice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (deviceId: string) => api.post<Device>(`/api/v1/devices/${deviceId}/revoke`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices"] }),
  });
}

export function useStartSession(deviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<DeviceSessionStart>(`/api/v1/devices/${deviceId}/sessions`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices", deviceId, "sessions"] }),
  });
}

export function useEndSession(deviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      api.post<DeviceSession>(`/api/v1/devices/${deviceId}/sessions/${sessionId}/end`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices", deviceId, "sessions"] }),
  });
}
