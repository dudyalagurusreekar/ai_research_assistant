"use client";

import { useAuthStore } from "@/stores/authStore";
import { Avatar } from "@/components/ui/avatar";
import { useTheme } from "next-themes";
import { Search, Bell, Sun, Moon, LogOut, Building2, User } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function Header() {
  const { user, logout, activeTenantId } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-border bg-card/60 px-6 backdrop-blur-xl">
      {/* Search Input */}
      <div className="flex items-center gap-3 w-96">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search tasks, documents, graph entities..."
            className="h-9 w-full rounded-lg border border-input bg-secondary/40 pl-9 pr-4 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-all"
          />
        </div>
      </div>

      {/* Right Controls & User Info */}
      <div className="flex items-center gap-4">
        {/* Active Tenant Selector */}
        <div className="flex items-center gap-2 rounded-lg border border-border bg-secondary/40 px-3 py-1.5 text-xs font-medium text-muted-foreground">
          <Building2 className="h-3.5 w-3.5 text-primary" />
          <span className="truncate max-w-[140px] text-foreground">{activeTenantId}</span>
        </div>

        {/* Notifications Bell */}
        <button className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-secondary/40 text-muted-foreground hover:text-foreground transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary animate-ping" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary" />
        </button>

        {/* Theme Switcher */}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-secondary/40 text-muted-foreground hover:text-foreground transition-colors"
        >
          {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-sky-400" />}
        </button>

        {/* User Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-3 rounded-lg p-1 hover:bg-secondary/60 transition-colors"
          >
            <Avatar name={user?.full_name || "User"} size="sm" />
            <div className="hidden md:flex flex-col text-left">
              <span className="text-xs font-semibold text-foreground">{user?.full_name || "Enterprise User"}</span>
              <span className="text-[10px] text-muted-foreground capitalize">{user?.role || "Researcher"}</span>
            </div>
          </button>

          {/* User Menu Popup */}
          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border border-border bg-card p-1.5 shadow-xl backdrop-blur-xl z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-3 py-2 border-b border-border/50">
                <p className="text-xs font-semibold text-foreground">{user?.full_name}</p>
                <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
              </div>
              <button
                onClick={() => { setShowUserMenu(false); router.push("/settings"); }}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
              >
                <User className="h-3.5 w-3.5" /> Profile Settings
              </button>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-destructive hover:bg-destructive/10 transition-colors"
              >
                <LogOut className="h-3.5 w-3.5" /> Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
