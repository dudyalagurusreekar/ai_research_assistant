"use client";

import React, { useState } from "react";
import { LiveBrowserViewer } from "@/features/browser/components/LiveBrowserViewer";
import { WorkflowBuilder } from "@/features/browser/components/WorkflowBuilder";
import { BrowserLogTerminal } from "@/features/browser/components/BrowserLogTerminal";
import { ExtractedDataViewer } from "@/features/browser/components/ExtractedDataViewer";
import { Globe, Cpu, Terminal, Database } from "lucide-react";

export default function BrowserStudioPage() {
  const [activeTab, setActiveTab] = useState<"live" | "workflow" | "data" | "logs">("live");

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Globe className="w-6 h-6 text-indigo-500" />
            Browser Automation Studio
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Playwright headless browser orchestration, drag-and-drop workflow designer, and structured JSON extractor
          </p>
        </div>
      </div>

      {/* Workspace Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("live")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "live" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Globe className="w-4 h-4" />
          Live Viewport Session
        </button>

        <button
          onClick={() => setActiveTab("workflow")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "workflow" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Cpu className="w-4 h-4" />
          Workflow Designer
        </button>

        <button
          onClick={() => setActiveTab("data")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "data" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Database className="w-4 h-4" />
          Extracted JSON & Screenshots
        </button>

        <button
          onClick={() => setActiveTab("logs")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "logs" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Terminal className="w-4 h-4" />
          Execution Logs Stream
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === "live" && (
        <div className="space-y-6">
          <LiveBrowserViewer />
          <WorkflowBuilder />
        </div>
      )}

      {activeTab === "workflow" && <WorkflowBuilder />}
      {activeTab === "data" && <ExtractedDataViewer />}
      {activeTab === "logs" && <BrowserLogTerminal />}
    </div>
  );
}
