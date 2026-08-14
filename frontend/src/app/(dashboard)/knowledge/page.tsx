"use client";

import React, { useState } from "react";
import { useKnowledgeStore, EntityType } from "@/store/use-knowledge-store";
import { GraphCanvas } from "@/features/knowledge/components/GraphCanvas";
import { EntityNodeInspector } from "@/features/knowledge/components/EntityNodeInspector";
import { LongTermMemoryView } from "@/features/knowledge/components/LongTermMemoryView";
import { GraphAnalyticsDashboard } from "@/features/knowledge/components/GraphAnalyticsDashboard";
import { Input } from "@/components/ui/Input";
import { Network, Brain, BarChart3, Search, Filter } from "lucide-react";

export default function KnowledgePage() {
  const { filterType, setFilterType, searchQuery, setSearchQuery } = useKnowledgeStore();
  const [activeTab, setActiveTab] = useState<"topology" | "memory" | "analytics">("topology");

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Network className="w-6 h-6 text-cyan-500" />
            Knowledge Graph Explorer & Memory Center
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            NetworkX property graph representation, PageRank centrality metrics, evidence provenance, and long-term memory
          </p>
        </div>
      </div>

      {/* Studio Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("topology")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "topology" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Network className="w-4 h-4" />
          Graph Topology Explorer
        </button>

        <button
          onClick={() => setActiveTab("memory")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "memory" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Brain className="w-4 h-4" />
          Long-Term Memory Platform
        </button>

        <button
          onClick={() => setActiveTab("analytics")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "analytics" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Centrality Analytics & Snapshots
        </button>
      </div>

      {/* Topology Explorer View */}
      {activeTab === "topology" && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="w-full sm:w-80">
              <Input
                placeholder="Search graph entities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={<Search className="w-4 h-4" />}
              />
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              {(["ALL", "PROTEIN", "GENE", "COMPOUND", "CELL_LINE", "PAPER"] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => setFilterType(type as any)}
                  className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
                    filterType === type
                      ? "bg-indigo-600 text-white shadow-glow-indigo"
                      : "bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 border border-slate-200 dark:border-slate-800"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <GraphCanvas />
            </div>
            <div>
              <EntityNodeInspector />
            </div>
          </div>
        </div>
      )}

      {activeTab === "memory" && <LongTermMemoryView />}
      {activeTab === "analytics" && <GraphAnalyticsDashboard />}
    </div>
  );
}
