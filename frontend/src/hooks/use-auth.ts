import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiUpload, ApiError } from "@/lib/api";
import type { LoginResult, Session, User } from "@/lib/types";

export const ME_QUERY_KEY = ["auth", "me"] as const;

export function useMe() {
  return useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: () => api.get<User>("/api/v1/auth/me"),
    retry: false,
    throwOnError: false,
  });
}

export function useIsAuthenticated() {
  const { data, isLoading, isError } = useMe();
  return { isAuthenticated: !!data && !isError, isLoading, user: data };
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { email: string; password: string }) => api.post<LoginResult>("/api/v1/auth/login", body),
    onSuccess: (data) => {
      if (data.user) queryClient.setQueryData(ME_QUERY_KEY, data.user);
    },
  });
}

export function useVerifyTwoFactorLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { two_factor_pending_token: string; code: string }) =>
      api.post<LoginResult>("/api/v1/auth/2fa/verify-login", body),
    onSuccess: (data) => {
      if (data.user) queryClient.setQueryData(ME_QUERY_KEY, data.user);
    },
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { email: string; password: string; full_name?: string }) =>
      api.post<User>("/api/v1/auth/register", body),
    onSuccess: (user) => {
      queryClient.setQueryData(ME_QUERY_KEY, user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/api/v1/auth/logout"),
    onSuccess: () => {
      queryClient.setQueryData(ME_QUERY_KEY, null);
      queryClient.clear();
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (body: { email: string }) => api.post<{ message: string }>("/api/v1/auth/forgot-password", body),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (body: { token: string; new_password: string }) =>
      api.post<{ message: string }>("/api/v1/auth/reset-password", body),
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: (body: { token: string }) => api.post<{ message: string }>("/api/v1/auth/verify-email", body),
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (body: { current_password: string; new_password: string }) =>
      api.post<{ message: string }>("/api/v1/auth/change-password", body),
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { full_name?: string }) => api.patch<User>("/api/v1/auth/me", body),
    onSuccess: (user) => queryClient.setQueryData(ME_QUERY_KEY, user),
  });
}

export function useUploadAvatar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiUpload<User>("/api/v1/auth/me/avatar", formData);
    },
    onSuccess: (user) => queryClient.setQueryData(ME_QUERY_KEY, user),
  });
}

export function useSessions() {
  return useQuery({
    queryKey: ["auth", "sessions"],
    queryFn: () => api.get<Session[]>("/api/v1/auth/sessions"),
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => api.delete(`/api/v1/auth/sessions/${sessionId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["auth", "sessions"] }),
  });
}

export function useSetupTwoFactor() {
  return useMutation({
    mutationFn: () =>
      api.post<{ secret: string; provisioning_uri: string; backup_codes: string[] }>("/api/v1/auth/2fa/setup"),
  });
}

export function useConfirmTwoFactor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (code: string) => api.post<{ message: string }>("/api/v1/auth/2fa/confirm", { code }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ME_QUERY_KEY }),
  });
}

export function useDisableTwoFactor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { password: string; code: string }) =>
      api.post<{ message: string }>("/api/v1/auth/2fa/disable", body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ME_QUERY_KEY }),
  });
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: (password: string) => api.delete<{ message: string }>("/api/v1/auth/me", { password }),
  });
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
