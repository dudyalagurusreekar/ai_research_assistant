"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUIStore } from "@/store/use-ui-store";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Microscope,
  FileText,
  Network,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  BrainCircuit,
  Globe,
  Link2,
  Sparkles,
  Dna,
  Boxes,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

const navItems: NavItem[] = [
  { name: "Overview", href: "/overview", icon: <LayoutDashboard className="w-5 h-5" /> },
  { name: "AI Chat Workspace", href: "/chat", icon: <BrainCircuit className="w-5 h-5" />, badge: "Live" },
  { name: "Genomic Variant Lab", href: "/genomics", icon: <Dna className="w-5 h-5" />, badge: "Alpha" },
  { name: "Protein 3D Studio", href: "/structure", icon: <Boxes className="w-5 h-5" />, badge: "PDB" },
  { name: "Reports Center", href: "/reports", icon: <FileText className="w-5 h-5" />, badge: "Exports" },
  { name: "Browser Studio", href: "/browser", icon: <Globe className="w-5 h-5" /> },
  { name: "Connectors Hub", href: "/connectors", icon: <Link2 className="w-5 h-5" /> },
  { name: "Research Workspace", href: "/research", icon: <Microscope className="w-5 h-5" /> },
  { name: "Documents & RAG", href: "/documents", icon: <FileText className="w-5 h-5" /> },
  { name: "Knowledge Graph", href: "/knowledge", icon: <Network className="w-5 h-5" /> },
  { name: "Data Intelligence", href: "/analytics", icon: <BarChart3 className="w-5 h-5" /> },
  { name: "Admin Dashboard", href: "/admin", icon: <Settings className="w-5 h-5" /> },
  { name: "Settings", href: "/settings", icon: <Settings className="w-5 h-5" /> },
];





export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <aside
      className={cn(
        "relative flex flex-col h-screen glass-panel border-r border-slate-200/80 dark:border-slate-800/80 transition-all duration-300 z-30 select-none",
        sidebarCollapsed ? "w-20" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-200/50 dark:border-slate-800/50">
        <Link href="/overview" className="flex items-center gap-3 overflow-hidden">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-glow-indigo shrink-0">
            <BrainCircuit className="w-6 h-6 animate-pulse-subtle" />
          </div>
          {!sidebarCollapsed && (
            <div className="flex flex-col">
              <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 bg-clip-text text-transparent">
                ARA v1.0
              </span>
              <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-widest">
                Research Assistant
              </span>
            </div>
          )}
        </Link>
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800/50 transition-colors"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 group relative",
                isActive
                  ? "bg-indigo-600 text-white shadow-glow-indigo font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/50 dark:hover:bg-slate-800/50"
              )}
              title={sidebarCollapsed ? item.name : undefined}
            >
              <span className={cn("shrink-0 transition-transform group-hover:scale-110", isActive && "text-white")}>
                {item.icon}
              </span>
              {!sidebarCollapsed && <span className="flex-1 truncate">{item.name}</span>}
              {!sidebarCollapsed && item.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold uppercase rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Banner */}
      {!sidebarCollapsed && (
        <div className="p-3 m-3 rounded-xl bg-gradient-to-br from-indigo-900/40 to-slate-900/60 border border-indigo-500/20 text-xs">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold mb-1">
            <Sparkles className="w-4 h-4" />
            <span>AI Platform GA</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Multi-agent research & knowledge graph ready.
          </p>
        </div>
      )}
    </aside>
  );
}
