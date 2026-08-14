import React, { ReactNode } from "react";
import Link from "next/link";
import { BrainCircuit } from "lucide-react";
import { ToastContainer } from "@/components/ui/Toast";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-4 sm:p-6 bg-slate-950 text-slate-100 relative overflow-hidden font-sans select-none">
      {/* Background Animated Gradient Blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none animate-pulse-subtle" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />

      {/* Brand Header */}
      <div className="relative z-10 flex flex-col items-center mb-6 text-center">
        <Link href="/" className="flex items-center gap-3 mb-2 group">
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-glow-indigo group-hover:scale-105 transition-transform">
            <BrainCircuit className="w-7 h-7" />
          </div>
          <span className="font-extrabold text-2xl tracking-tight bg-gradient-to-r from-indigo-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">
            ARA v1.0
          </span>
        </Link>
        <p className="text-xs text-slate-400 font-medium tracking-wide">
          AI Research Assistant Platform
        </p>
      </div>

      {/* Card Container */}
      <div className="relative z-10 w-full max-w-md">
        {children}
      </div>

      <ToastContainer />
    </div>
  );
}
