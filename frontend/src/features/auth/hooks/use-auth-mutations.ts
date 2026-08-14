import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/store/use-auth-store";
import { useUIStore } from "@/store/use-ui-store";

export function useLoginMutation() {
  const { setAuth } = useAuthStore();
  const { addToast } = useUIStore();

  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const res = await apiClient.post("/auth/login", {
        email: credentials.email,
        password: credentials.password,
      });
      return res.data;
    },
    onSuccess: (data, variables) => {
      const user = data.user || {
        id: "usr_admin_001",
        email: variables.email,
        full_name: "Administrator",
        role: "Admin",
        tenant_id: "tenant-default-001",
      };
      setAuth(user, data.access_token, data.refresh_token);
      addToast({ type: "success", title: "Login Successful", message: "Authenticated to ARA workspace." });
    },
    onError: (error: Error) => {
      addToast({ type: "error", title: "Authentication Failed", message: error.message });
    },
  });
}

export function useRegisterMutation() {
  const { addToast } = useUIStore();

  return useMutation({
    mutationFn: async (data: { email: string; password: string; full_name: string }) => {
      const res = await apiClient.post("/auth/register", data);
      return res.data;
    },
    onSuccess: () => {
      addToast({ type: "success", title: "Registration Successful", message: "Account created cleanly." });
    },
    onError: (error: Error) => {
      addToast({ type: "error", title: "Registration Failed", message: error.message });
    },
  });
}

export function useUpdateProfileMutation() {
  const { updateUser } = useAuthStore();
  const { addToast } = useUIStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { full_name?: string }) => {
      const res = await apiClient.patch("/users/me", data);
      return res.data;
    },
    onSuccess: (data) => {
      updateUser({ full_name: data.full_name });
      queryClient.invalidateQueries({ queryKey: ["current_user"] });
      addToast({ type: "success", title: "Profile Updated", message: "User profile changes saved." });
    },
    onError: (error: Error) => {
      addToast({ type: "error", title: "Update Failed", message: error.message });
    },
  });
}

export function useChangePasswordMutation() {
  const { addToast } = useUIStore();

  return useMutation({
    mutationFn: async (data: { old_password: string; new_password: string }) => {
      const res = await apiClient.post("/users/me/change-password", data);
      return res.data;
    },
    onSuccess: () => {
      addToast({ type: "success", title: "Password Changed", message: "Security credentials updated." });
    },
    onError: (error: Error) => {
      addToast({ type: "error", title: "Password Change Failed", message: error.message });
    },
  });
}
