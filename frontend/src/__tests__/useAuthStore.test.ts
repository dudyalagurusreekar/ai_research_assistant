import { useAuthStore } from "@/store/use-auth-store";

describe("useAuthStore Zustand Store", () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
  });

  it("sets authentication state correctly", () => {
    const mockUser = {
      id: "usr_test_1",
      email: "test@ara.org",
      full_name: "Test User",
      role: "Researcher",
    };

    useAuthStore.getState().setAuth(mockUser, "test_access", "test_refresh");

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.email).toBe("test@ara.org");
    expect(state.accessToken).toBe("test_access");
  });

  it("clears authentication state on logout", () => {
    const mockUser = {
      id: "usr_test_1",
      email: "test@ara.org",
      full_name: "Test User",
      role: "Researcher",
    };

    useAuthStore.getState().setAuth(mockUser, "test_access", "test_refresh");
    useAuthStore.getState().clearAuth();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
  });
});
