"use client";

import React, { useState } from "react";
import { useDataStore } from "@/store/use-data-store";
import { DatasetProfiler } from "@/features/analytics/components/DatasetProfiler";
import { DataVisualizationStudio } from "@/features/analytics/components/DataVisualizationStudio";
import { SQLQueryWorkspace } from "@/features/analytics/components/SQLQueryWorkspace";
import { AIDataAnalyst } from "@/features/analytics/components/AIDataAnalyst";
import { BarChart3, Database, Code, Sparkles, Table } from "lucide-react";

export default function AnalyticsPage() {
  const { datasets, selectedDataset, setSelectedDataset } = useDataStore();
  const activeDataset = selectedDataset || datasets[0];
  const [activeTab, setActiveTab] = useState<"profiler" | "viz" | "sql" | "analyst">("profiler");

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-indigo-500" />
            Data Intelligence Studio
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Automated schema profiling, interactive visualization, Text-to-SQL DuckDB engine, and AI statistical analysis
          </p>
        </div>

        {/* Dataset Selector */}
        <select
          value={activeDataset.id}
          onChange={(e) => {
            const found = datasets.find((d) => d.id === e.target.value);
            if (found) setSelectedDataset(found);
          }}
          className="text-xs font-semibold p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none"
        >
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      {/* Studio Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("profiler")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "profiler" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Table className="w-4 h-4" />
          Schema & Profiling
        </button>

        <button
          onClick={() => setActiveTab("viz")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "viz" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Visualization Studio
        </button>

        <button
          onClick={() => setActiveTab("sql")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "sql" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Code className="w-4 h-4" />
          Text-to-SQL Editor
        </button>

        <button
          onClick={() => setActiveTab("analyst")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "analyst" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          AI Data Analyst & Anomalies
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === "profiler" && <DatasetProfiler dataset={activeDataset} />}
      {activeTab === "viz" && <DataVisualizationStudio />}
      {activeTab === "sql" && <SQLQueryWorkspace />}
      {activeTab === "analyst" && <AIDataAnalyst />}
    </div>
  );
}
