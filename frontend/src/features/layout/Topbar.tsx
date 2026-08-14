"use client";

import React, { useState } from "react";
import { useTheme } from "next-themes";
import { useAuthStore } from "@/store/use-auth-store";
import { useRouter } from "next/navigation";
import {
  Search,
  Sun,
  Moon,
  Laptop,
  Bell,
  LogOut,
  User as UserIcon,
  Shield,
  ChevronDown,
} from "lucide-react";
import { GlobalSearchModal } from "@/features/dashboard/components/GlobalSearchModal";
import { NotificationDrawer } from "@/features/dashboard/components/NotificationDrawer";

export function Topbar() {
  const { theme, setTheme } = useTheme();
  const { user, clearAuth } = useAuthStore();
  const router = useRouter();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const handleLogout = () => {
    clearAuth();
    router.push("/login");
  };

  return (
    <>
      <header className="sticky top-0 z-20 flex items-center justify-between h-16 px-6 glass-panel border-b border-slate-200/80 dark:border-slate-800/80">
        {/* Global Search Bar */}
        <div className="relative w-72 sm:w-96 cursor-pointer" onClick={() => setSearchOpen(true)}>
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500 pointer-events-none" />
          <input
            type="text"
            readOnly
            placeholder="Search research, entities, documents... (Ctrl+K)"
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-900/90 text-sm text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 cursor-pointer focus:outline-none placeholder:text-slate-400"
          />
        </div>

        {/* Right Action Icons & User Dropdown */}
        <div className="flex items-center gap-3">
          {/* Theme Switcher */}
          <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800">
            <button
              onClick={() => setTheme("light")}
              className={`p-1.5 rounded-lg transition-colors ${
                theme === "light" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-400 hover:text-slate-600"
              }`}
              title="Light Theme"
            >
              <Sun className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTheme("dark")}
              className={`p-1.5 rounded-lg transition-colors ${
                theme === "dark" ? "bg-slate-800 text-indigo-400 shadow-sm" : "text-slate-400 hover:text-slate-600"
              }`}
              title="Dark Theme"
            >
              <Moon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTheme("system")}
              className={`p-1.5 rounded-lg transition-colors ${
                theme === "system" ? "bg-white dark:bg-slate-800 text-indigo-600 shadow-sm" : "text-slate-400"
              }`}
              title="System Theme"
            >
              <Laptop className="w-4 h-4" />
            </button>
          </div>

          {/* Notifications Toggle */}
          <button
            onClick={() => setNotificationsOpen(true)}
            className="relative p-2 rounded-xl text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
          </button>

          {/* User Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2.5 p-1.5 pl-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/80 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white font-bold text-xs shadow-sm">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "A"}
              </div>
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {user?.full_name || "Admin User"}
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400">
                  {user?.role || "Researcher"}
                </span>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 glass-panel rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 py-1.5 animate-slide-up z-50">
                <div className="px-3.5 py-2 border-b border-slate-200/50 dark:border-slate-800/50">
                  <p className="text-xs font-bold text-slate-900 dark:text-slate-100">
                    {user?.email || "admin@ara-research.org"}
                  </p>
                  <div className="flex items-center gap-1.5 mt-0.5 text-[10px] text-indigo-500 font-semibold">
                    <Shield className="w-3 h-3" />
                    <span>Tenant: {user?.tenant_id || "default-tenant"}</span>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setUserMenuOpen(false);
                    router.push("/settings");
                  }}
                  className="flex items-center gap-2.5 w-full px-3.5 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <UserIcon className="w-4 h-4" />
                  Profile Settings
                </button>

                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2.5 w-full px-3.5 py-2 text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 transition-colors border-t border-slate-200/50 dark:border-slate-800/50 mt-1"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Modals & Drawers */}
      <GlobalSearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
      <NotificationDrawer isOpen={notificationsOpen} onClose={() => setNotificationsOpen(false)} />
    </>
  );
}
