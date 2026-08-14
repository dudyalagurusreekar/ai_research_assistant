"use client";

import React, { useState } from "react";
import { useReportsStore } from "@/store/use-reports-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { ShieldCheck, Activity, Users, DollarSign, Search, Clock, Server } from "lucide-react";

export default function AdminDashboardPage() {
  const { auditLogs } = useReportsStore();
  const [filterType, setFilterType] = useState<string>("ALL");

  const filteredLogs = auditLogs.filter((log) => filterType === "ALL" || log.event_type === filterType);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-indigo-500" />
            Administrator Control Center & System Telemetry
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            System load, active user sessions, token expenditure, and audit logs
          </p>
        </div>
      </div>

      {/* Admin Telemetry Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card variant="glass">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400">Active Users</span>
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <h3 className="text-3xl font-black text-slate-100">12 Online</h3>
          <p className="text-[11px] text-emerald-400 mt-1">RBAC Active</p>
        </Card>

        <Card variant="glass">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400">System Load</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <h3 className="text-3xl font-black text-slate-100">14.2% CPU</h3>
          <p className="text-[11px] text-cyan-400 mt-1">4.2 GB / 16 GB RAM</p>
        </Card>

        <Card variant="glass">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400">Monthly AI Cost</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <h3 className="text-3xl font-black text-emerald-400">$18.42</h3>
          <p className="text-[11px] text-slate-400 mt-1">4.2M Tokens Processed</p>
        </Card>

        <Card variant="glass">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400">Prometheus Health</span>
            <Server className="w-4 h-4 text-amber-400" />
          </div>
          <h3 className="text-3xl font-black text-slate-100">100% OK</h3>
          <p className="text-[11px] text-emerald-400 mt-1">0 Server Crashes</p>
        </Card>
      </div>

      {/* Audit Logs Table */}
      <Card variant="glass">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle>System Audit Logs</CardTitle>
            <CardDescription>Security events, login attempts, AI request telemetry, and settings changes</CardDescription>
          </div>

          <div className="flex items-center gap-2">
            {(["ALL", "LOGIN", "AI_REQUEST", "REPORT_GEN", "SETTINGS_CHANGE"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${
                  filterType === t ? "bg-indigo-600 text-white shadow-glow-indigo" : "bg-slate-900 text-slate-400"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </CardHeader>

        <CardContent>
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Event Type</th>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Details</th>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200 font-mono">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-900/40">
                    <td className="px-4 py-3">
                      <Badge variant="brand">{log.event_type}</Badge>
                    </td>
                    <td className="px-4 py-3 font-bold text-slate-100">{log.user}</td>
                    <td className="px-4 py-3 text-slate-300">{log.details}</td>
                    <td className="px-4 py-3 text-slate-400">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="success">{log.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
