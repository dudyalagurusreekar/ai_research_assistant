"use client";

import React from "react";
import { useChatStore } from "@/store/use-chat-store";
import { Badge } from "@/components/ui/Badge";
import { X, Cpu, CheckCircle2, Clock, Sparkles } from "lucide-react";

export function ExecutionTimeline() {
  const { showExecutionTimeline, toggleExecutionTimeline } = useChatStore();

  if (!showExecutionTimeline) return null;

  const steps = [
    { step: 1, name: "Query Parsing & Intent Detection", status: "Completed", latency: "12ms" },
    { step: 2, name: "FastAPI RAG Vector Retrieval (1536-dim)", status: "Completed", latency: "45ms" },
    { step: 3, name: "spaCy Named Entity Recognition", status: "Completed", latency: "28ms" },
    { step: 4, name: "NetworkX Centrality Calculation", status: "Completed", latency: "14ms" },
    { step: 5, name: "LLM Response Generation & Audit", status: "Completed", latency: "120ms" },
  ];

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-80 glass-panel shadow-2xl border-l border-slate-200/80 dark:border-slate-800/80 p-5 animate-slide-up flex flex-col">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-100">Agent Execution Timeline</h3>
        </div>
        <button onClick={toggleExecutionTimeline} className="text-slate-400 hover:text-slate-200">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 py-4 space-y-3 overflow-y-auto">
        {steps.map((s) => (
          <div key={s.step} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-indigo-400">Step {s.step}</span>
              <Badge variant="success" size="sm">{s.status}</Badge>
            </div>
            <p className="text-xs font-bold text-slate-200">{s.name}</p>
            <span className="text-[10px] text-slate-400 flex items-center gap-1">
              <Clock className="w-3 h-3" /> Execution Latency: {s.latency}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
