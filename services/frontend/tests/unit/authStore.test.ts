import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "../../src/stores/authStore";

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  it("should initialize with default unauthenticated state", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.accessToken).toBeNull();
  });

  it("should set user profile and access token on setAuth", () => {
    const mockUser = {
      id: "usr_test_123",
      email: "researcher@ara-platform.org",
      full_name: "Dr. Alice Turing",
      role: "Researcher",
      is_active: true,
    };

    useAuthStore.getState().setAuth(mockUser, "test_jwt_access_token");

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.email).toBe("researcher@ara-platform.org");
    expect(state.accessToken).toBe("test_jwt_access_token");
  });

  it("should clear state on logout", () => {
    const mockUser = {
      id: "usr_test_123",
      email: "researcher@ara-platform.org",
      full_name: "Dr. Alice Turing",
      role: "Researcher",
      is_active: true,
    };

    useAuthStore.getState().setAuth(mockUser, "test_jwt_access_token");
    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.accessToken).toBeNull();
  });
});
