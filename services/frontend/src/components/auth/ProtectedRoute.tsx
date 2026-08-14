"use client";

import { useAuthStore } from "@/stores/authStore";
import { useRouter } from "next/navigation";
import { useEffect, useState, ReactNode } from "react";
import { Loader2 } from "lucide-react";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, initialize } = useAuthStore();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    initialize();
    const token = localStorage.getItem("ara_access_token");
    if (!token) {
      router.push("/login");
    } else {
      setIsChecking(false);
    }
  }, [router, initialize]);

  if (isChecking && !isAuthenticated) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm font-medium text-muted-foreground">Verifying enterprise credentials...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
