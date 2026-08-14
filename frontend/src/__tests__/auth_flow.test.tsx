import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { useAuthStore } from "@/store/use-auth-store";

describe("Sprint F2: Authentication & User Flow Verification", () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
  });

  it("verifies user session state initialization and mutation", () => {
    const mockUser = {
      id: "usr_f2_test",
      email: "test.f2@ara-research.org",
      full_name: "Sprint F2 Tester",
      role: "Researcher",
      tenant_id: "tenant-default-001",
    };

    useAuthStore.getState().setAuth(mockUser, "access_f2_token", "refresh_f2_token");

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.full_name).toBe("Sprint F2 Tester");
    expect(state.accessToken).toBe("access_f2_token");
  });

  it("verifies profile update mutation logic in store", () => {
    const mockUser = {
      id: "usr_f2_test",
      email: "test.f2@ara-research.org",
      full_name: "Original Name",
      role: "Researcher",
    };

    useAuthStore.getState().setAuth(mockUser, "token", "refresh");
    useAuthStore.getState().updateUser({ full_name: "Updated Name" });

    const state = useAuthStore.getState();
    expect(state.user?.full_name).toBe("Updated Name");
  });
});
