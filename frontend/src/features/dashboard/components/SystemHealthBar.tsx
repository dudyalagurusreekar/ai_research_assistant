"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Server, Database, HardDrive, Activity, CheckCircle2 } from "lucide-react";

export function SystemHealthBar() {
  const services = [
    { name: "FastAPI Router Engine", status: "Healthy", icon: <Server className="w-4 h-4 text-emerald-400" /> },
    { name: "Postgres + pgvector", status: "Connected", icon: <Database className="w-4 h-4 text-cyan-400" /> },
    { name: "MinIO S3 Buckets", status: "Online", icon: <HardDrive className="w-4 h-4 text-indigo-400" /> },
    { name: "Prometheus Metrics", status: "Scraping", icon: <Activity className="w-4 h-4 text-amber-400" /> },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {services.map((s, i) => (
        <div
          key={i}
          className="flex items-center justify-between p-3.5 rounded-xl glass-panel border border-slate-200/60 dark:border-slate-800/80 shadow-sm"
        >
          <div className="flex items-center gap-2.5">
            {s.icon}
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">{s.name}</span>
          </div>
          <Badge variant="success" size="sm" className="gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>{s.status}</span>
          </Badge>
        </div>
      ))}
    </div>
  );
}
