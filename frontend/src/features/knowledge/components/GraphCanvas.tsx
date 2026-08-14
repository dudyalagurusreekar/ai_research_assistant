"use client";

import React from "react";
import { GraphNode, useKnowledgeStore, EntityType } from "@/store/use-knowledge-store";
import { Badge } from "@/components/ui/Badge";
import { Cpu, GitBranch, Dna, FlaskConical, FileText, ZoomIn, ZoomOut, RefreshCw } from "lucide-react";

export function GraphCanvas() {
  const { nodes, edges, selectedNode, setSelectedNode, filterType, searchQuery } = useKnowledgeStore();

  const filteredNodes = nodes.filter((n) => {
    const matchesFilter = filterType === "ALL" || n.type === filterType;
    const matchesSearch = n.name.toLowerCase().includes(searchQuery.toLowerCase()) || n.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getEntityIcon = (type: EntityType) => {
    switch (type) {
      case "PROTEIN":
        return <Cpu className="w-5 h-5 text-indigo-400" />;
      case "GENE":
        return <Dna className="w-5 h-5 text-cyan-400" />;
      case "COMPOUND":
        return <FlaskConical className="w-5 h-5 text-emerald-400" />;
      case "CELL_LINE":
        return <GitBranch className="w-5 h-5 text-amber-400" />;
      case "PAPER":
        return <FileText className="w-5 h-5 text-purple-400" />;
      default:
        return <Cpu className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="glass-card rounded-2xl border border-slate-200/80 dark:border-slate-800/80 overflow-hidden relative">
      {/* Canvas Viewport Controls */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800 text-xs">
        <span className="font-bold text-slate-200">NetworkX Property Graph Viewport ({filteredNodes.length} Nodes)</span>
        <div className="flex items-center gap-2">
          <button className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <ZoomOut className="w-4 h-4" />
          </button>
          <button className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Visual Canvas Representation */}
      <div className="h-[460px] bg-slate-950 relative flex items-center justify-center p-6 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(#3730a3_1px,transparent_1px)] [background-size:20px_20px] opacity-20" />

        {/* SVG Relation Connector Lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
          <defs>
            <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.6" />
            </linearGradient>
            <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1" />
            </marker>
          </defs>
          <line x1="25%" y1="35%" x2="50%" y2="35%" stroke="url(#edgeGradient)" strokeWidth="2" strokeDasharray="4" markerEnd="url(#arrow)" />
          <line x1="50%" y1="35%" x2="75%" y2="35%" stroke="url(#edgeGradient)" strokeWidth="2" strokeDasharray="4" markerEnd="url(#arrow)" />
          <line x1="35%" y1="65%" x2="65%" y2="65%" stroke="url(#edgeGradient)" strokeWidth="2" strokeDasharray="4" markerEnd="url(#arrow)" />
        </svg>

        {/* Edge Badges Overlay */}
        <div className="absolute top-16 left-1/3 z-10 -translate-x-1/2">
          <span className="px-2 py-0.5 rounded-full bg-indigo-900/80 border border-indigo-500/50 text-[10px] font-mono font-bold text-indigo-300 shadow-sm">
            TARGETS (98%)
          </span>
        </div>
        <div className="absolute top-16 right-1/3 z-10 translate-x-1/2">
          <span className="px-2 py-0.5 rounded-full bg-cyan-900/80 border border-cyan-500/50 text-[10px] font-mono font-bold text-cyan-300 shadow-sm">
            TARGETS (94%)
          </span>
        </div>

        {/* Nodes Cluster */}
        <div className="relative z-10 flex flex-wrap items-center justify-center gap-6 max-w-2xl">
          {filteredNodes.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            return (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className={`p-4 rounded-2xl border cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? "bg-indigo-600/30 border-indigo-500 shadow-glow-indigo scale-105"
                    : "bg-slate-900/80 border-slate-800 hover:border-slate-700 hover:scale-102"
                }`}
              >
                <div className="flex items-center gap-2.5 mb-2">
                  {getEntityIcon(node.type)}
                  <div>
                    <h4 className="text-xs font-bold text-slate-100">{node.name}</h4>
                    <span className="text-[10px] text-slate-400 uppercase font-mono">{node.type}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3 text-[10px] text-slate-400 pt-2 border-t border-slate-800">
                  <span>PageRank: <strong className="text-indigo-400">{node.pagerank_score}</strong></span>
                  <span>Degree: <strong className="text-cyan-400">{node.degree}</strong></span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
