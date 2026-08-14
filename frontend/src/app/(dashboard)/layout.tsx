import React, { ReactNode } from "react";
import { AppShell } from "@/features/layout/AppShell";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
