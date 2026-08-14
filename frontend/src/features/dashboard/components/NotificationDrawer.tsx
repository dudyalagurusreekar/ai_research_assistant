"use client";

import React, { useState } from "react";
import { NotificationItem } from "../services/dashboard-service";
import { Badge } from "@/components/ui/Badge";
import { X, Bell, CheckCircle2, Info, AlertTriangle, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

export function NotificationDrawer({
  isOpen,
  onClose,
  notifications,
}: {
  isOpen: boolean;
  onClose: () => void;
  notifications?: NotificationItem[];
}) {
  const router = useRouter();
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const items: NotificationItem[] = notifications || [
    {
      id: "notif_1",
      title: "Knowledge Graph Update",
      message: "Extracted 42 new gene entities from bioRxiv paper",
      type: "info",
      read: false,
      timestamp: "5 mins ago",
      link: "/knowledge",
    },
    {
      id: "notif_2",
      title: "Sprint 13 Release Benchmark Passed",
      message: "150/150 evaluation tasks passed cleanly (100% Quality)",
      type: "success",
      read: false,
      timestamp: "1 hour ago",
      link: "/overview",
    },
  ];

  const filtered = items.filter((n) => (filter === "unread" ? !n.read : true));

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-80 sm:w-96 glass-panel shadow-2xl border-l border-slate-200/80 dark:border-slate-800/80 p-5 animate-slide-up flex flex-col">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-100">Notifications & Alerts</h3>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 pt-3 pb-1">
        <button
          onClick={() => setFilter("all")}
          className={`px-3 py-1 rounded-lg text-xs font-bold ${filter === "all" ? "bg-indigo-600 text-white" : "text-slate-400"}`}
        >
          All
        </button>
        <button
          onClick={() => setFilter("unread")}
          className={`px-3 py-1 rounded-lg text-xs font-bold ${filter === "unread" ? "bg-indigo-600 text-white" : "text-slate-400"}`}
        >
          Unread
        </button>
      </div>

      {/* Notification List */}
      <div className="flex-1 py-3 space-y-3 overflow-y-auto">
        {filtered.map((item) => (
          <div
            key={item.id}
            onClick={() => {
              if (item.link) {
                onClose();
                router.push(item.link);
              }
            }}
            className={`p-3.5 rounded-xl border cursor-pointer transition-colors ${
              !item.read
                ? "bg-indigo-600/10 border-indigo-500/30"
                : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-xs font-bold text-slate-100">{item.title}</h4>
              <span className="text-[10px] text-slate-500">{item.timestamp}</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mb-2">{item.message}</p>

            {item.link && (
              <span className="text-[11px] font-semibold text-indigo-400 hover:underline flex items-center gap-1">
                View Artifact <ArrowRight className="w-3 h-3" />
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
