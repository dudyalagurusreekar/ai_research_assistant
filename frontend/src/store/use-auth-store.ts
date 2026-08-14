import { create } from "zustand";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id?: string;
  avatar_url?: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
  updateUser: (partialUser: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: typeof window !== "undefined" ? JSON.parse(localStorage.getItem("ara_user") || "null") : null,
  accessToken: typeof window !== "undefined" ? localStorage.getItem("ara_access_token") : null,
  refreshToken: typeof window !== "undefined" ? localStorage.getItem("ara_refresh_token") : null,
  isAuthenticated: typeof window !== "undefined" ? !!localStorage.getItem("ara_access_token") : false,
  isLoading: false,

  setAuth: (user, accessToken, refreshToken) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("ara_user", JSON.stringify(user));
      localStorage.setItem("ara_access_token", accessToken);
      localStorage.setItem("ara_refresh_token", refreshToken);
    }
    set({
      user,
      accessToken,
      refreshToken,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  clearAuth: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("ara_user");
      localStorage.removeItem("ara_access_token");
      localStorage.removeItem("ara_refresh_token");
    }
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  updateUser: (partialUser) => {
    set((state) => {
      if (!state.user) return state;
      const updatedUser = { ...state.user, ...partialUser };
      if (typeof window !== "undefined") {
        localStorage.setItem("ara_user", JSON.stringify(updatedUser));
      }
      return { user: updatedUser };
    });
  },
}));
