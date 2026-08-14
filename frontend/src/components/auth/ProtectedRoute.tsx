"use client";

import React, { useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/use-auth-store";
import { Spinner } from "@/components/ui/Spinner";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRoles?: string[];
}

export function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(`/login?redirect=${encodeURIComponent(pathname || "/overview")}`);
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
        <div className="flex flex-col items-center gap-3">
          <Spinner size="lg" />
          <span className="text-xs font-semibold text-slate-400">Verifying session security...</span>
        </div>
      </div>
    );
  }

  if (requiredRoles && requiredRoles.length > 0 && user) {
    const hasRole = requiredRoles.includes(user.role);
    if (!hasRole) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6 text-center">
          <div className="glass-card p-6 max-w-md border-rose-500/30">
            <h3 className="text-lg font-bold text-rose-500 mb-2">Access Restricted</h3>
            <p className="text-xs text-slate-400">
              Your role ({user.role}) does not have permission to view this section. Requires: {requiredRoles.join(", ")}
            </p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}
