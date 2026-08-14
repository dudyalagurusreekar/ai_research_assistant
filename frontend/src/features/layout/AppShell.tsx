"use client";

import React, { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { ToastContainer } from "@/components/ui/Toast";
import { ErrorBoundary } from "@/components/feedback/ErrorBoundary";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Workspace Area */}
      <div className="flex flex-col flex-1 h-screen overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>

      {/* Toast Notification Container */}
      <ToastContainer />
    </div>
  );
}
