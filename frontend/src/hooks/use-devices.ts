import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Device,
  DeviceSession,
  DeviceSessionStart,
  Paginated,
  PairingCodeCreated,
} from "@/lib/types";

/**
 * The device is considered online if it checked in within this window. The
 * Android client polls /sessions/pending every 3s while sharing is toggled
 * on, and each poll refreshes last_seen_at — so this is really "is the app
 * open and ready to accept a session", which is exactly what decides whether
 * pressing Connect will do anything.
 */
export const DEVICE_ONLINE_WINDOW_MS = 15_000;

export function isDeviceOnline(device: Device): boolean {
  if (!device.is_active || !device.last_seen_at) return false;
  return Date.now() - new Date(device.last_seen_at).getTime() < DEVICE_ONLINE_WINDOW_MS;
}

export function useDevices(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["devices", page, pageSize],
    queryFn: () => api.get<Paginated<Device>>(`/api/v1/devices?page=${page}&page_size=${pageSize}`),
    placeholderData: (prev) => prev,
    // Keeps the online dots honest without the user having to reload.
    refetchInterval: 5_000,
  });
}

/** There is no single-device endpoint; the list is small and already cached. */
export function useDevice(deviceId: string | undefined) {
  const { data, ...rest } = useDevices(1, 100);
  return { ...rest, data: data?.items.find((device) => device.id === deviceId) };
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
