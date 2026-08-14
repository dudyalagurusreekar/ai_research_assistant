"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  FlaskConical,
  Network,
  Scale,
  Activity,
  Cable,
  Settings,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Research Workspace", href: "/workspace", icon: FlaskConical, badge: "AI Core" },
  { label: "GraphRAG Explorer", href: "/graph", icon: Network },
  { label: "Decision Matrix", href: "/decisions", icon: Scale },
  { label: "Evaluation & QA", href: "/eval", icon: Activity, badge: "v1.0" },
  { label: "Connectors", href: "/connectors", icon: Cable },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-border bg-card/60 backdrop-blur-xl transition-all duration-300 z-30 select-none",
        isCollapsed ? "w-20" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border/50">
        <Link href="/dashboard" className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-md shadow-primary/30 shrink-0">
            <Sparkles className="h-5 w-5" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-wide text-foreground">ARA Enterprise</span>
              <span className="text-[10px] text-muted-foreground font-mono">v1.0 Platform</span>
            </div>
          )}
        </Link>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-secondary/50 text-muted-foreground hover:text-foreground transition-colors"
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all group relative",
                isActive
                  ? "bg-primary/10 text-primary border border-primary/20 shadow-sm"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
              )}
            >
              <Icon className={cn("h-5 w-5 shrink-0 transition-colors", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
              {!isCollapsed && (
                <div className="flex flex-1 items-center justify-between overflow-hidden">
                  <span className="truncate">{item.label}</span>
                  {item.badge && (
                    <span className="rounded-full bg-primary/20 px-2 py-0.5 text-[10px] font-semibold text-primary">
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Security Status Badge */}
      {!isCollapsed && (
        <div className="p-3 border-t border-border/50">
          <div className="flex items-center gap-2.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-2.5 text-xs text-emerald-400">
            <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
            <div className="flex flex-col">
              <span className="font-semibold">Security Gate Active</span>
              <span className="text-[10px] opacity-80">RBAC & Tenant Isolation</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
