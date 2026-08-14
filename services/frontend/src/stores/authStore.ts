import { create } from "zustand";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id?: string;
  is_active: boolean;
}

interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  activeWorkspaceId: string | null;
  activeTenantId: string | null;
  
  // Actions
  setAuth: (user: UserProfile, accessToken: string, refreshToken?: string) => void;
  logout: () => void;
  setActiveWorkspace: (workspaceId: string) => void;
  setActiveTenant: (tenantId: string) => void;
  initialize: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  activeWorkspaceId: null,
  activeTenantId: "tenant_default_enterprise",

  setAuth: (user, accessToken, refreshToken) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("ara_access_token", accessToken);
      if (refreshToken) localStorage.setItem("ara_refresh_token", refreshToken);
      localStorage.setItem("ara_user_profile", JSON.stringify(user));
    }
    set({
      user,
      accessToken,
      refreshToken: refreshToken || null,
      isAuthenticated: true,
      activeTenantId: user.tenant_id || "tenant_default_enterprise",
    });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("ara_access_token");
      localStorage.removeItem("ara_refresh_token");
      localStorage.removeItem("ara_user_profile");
    }
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      activeWorkspaceId: null,
    });
  },

  setActiveWorkspace: (workspaceId) => set({ activeWorkspaceId: workspaceId }),
  setActiveTenant: (tenantId) => set({ activeTenantId: tenantId }),

  initialize: () => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("ara_access_token");
      const userStr = localStorage.getItem("ara_user_profile");
      if (token && userStr) {
        try {
          const user = JSON.parse(userStr);
          set({
            user,
            accessToken: token,
            isAuthenticated: true,
            activeTenantId: user.tenant_id || "tenant_default_enterprise",
          });
        } catch {
          localStorage.removeItem("ara_access_token");
          localStorage.removeItem("ara_user_profile");
        }
      }
    }
  },
}));
