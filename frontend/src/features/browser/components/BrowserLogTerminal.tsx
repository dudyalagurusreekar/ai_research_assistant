"use client";

import React from "react";
import { useBrowserStore } from "@/store/use-browser-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Terminal, Trash2 } from "lucide-react";

export function BrowserLogTerminal() {
  const { logs, clearLogs } = useBrowserStore();

  return (
    <Card variant="glass" className="space-y-3">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-emerald-400" />
            Playwright Execution Logs & Network Stream
          </CardTitle>
          <CardDescription>Structured event telemetry stream from browser session</CardDescription>
        </div>

        <button
          onClick={clearLogs}
          className="text-xs font-semibold text-slate-400 hover:text-slate-200 flex items-center gap-1"
        >
          <Trash2 className="w-3.5 h-3.5" /> Clear Logs
        </button>
      </CardHeader>

      <CardContent>
        <div className="h-64 rounded-xl bg-slate-950 p-4 font-mono text-xs text-emerald-400 overflow-y-auto space-y-1.5 border border-slate-800">
          {logs.map((log, i) => (
            <div key={i} className="leading-relaxed">
              <span className="text-slate-500 mr-2">[{new Date().toLocaleTimeString()}]</span>
              <span className={log.includes("SUCCESS") ? "text-emerald-400 font-bold" : log.includes("START") ? "text-cyan-400" : "text-slate-300"}>
                {log}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
