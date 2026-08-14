"use client";

import React, { useState, useEffect } from "react";
import { Search, X, Microscope, Network, FileText, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

export function GlobalSearchModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const searchItems = [
    { title: "CRISPR-Cas9 Off-Target Specificity", type: "Research Session", href: "/research", icon: <Microscope className="w-4 h-4 text-indigo-400" /> },
    { title: "EMX1 Gene Target Cleavage", type: "Graph Entity", href: "/knowledge", icon: <Network className="w-4 h-4 text-cyan-400" /> },
    { title: "AlphaFold3_Structure_Analysis.pdf", type: "RAG Document", href: "/documents", icon: <FileText className="w-4 h-4 text-emerald-400" /> },
    { title: "OpenFDA Adverse Reaction Telemetry", type: "Data Analytics", href: "/analytics", icon: <Search className="w-4 h-4 text-amber-400" /> },
  ];

  const filtered = searchItems.filter(
    (item) => item.title.toLowerCase().includes(query.toLowerCase()) || item.type.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (isOpen) onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 sm:p-6 animate-fade-in">
      <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-10 w-full max-w-xl glass-panel rounded-2xl p-4 shadow-2xl border border-slate-200/50 dark:border-slate-800 space-y-4 animate-slide-up">
        {/* Search Input Bar */}
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            autoFocus
            placeholder="Search projects, sessions, knowledge graph entities, documents..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-3 rounded-xl bg-slate-100 dark:bg-slate-900 text-sm text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button onClick={onClose} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="space-y-1.5 max-h-80 overflow-y-auto">
          {filtered.length > 0 ? (
            filtered.map((item, idx) => (
              <div
                key={idx}
                onClick={() => {
                  onClose();
                  router.push(item.href);
                }}
                className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/80 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-slate-200/50 dark:bg-slate-900 border border-slate-300 dark:border-slate-800">
                    {item.icon}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">{item.title}</h4>
                    <span className="text-[10px] text-slate-500 uppercase font-semibold tracking-wider">{item.type}</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400" />
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-xs text-slate-400">No matching research artifacts found.</div>
          )}
        </div>
      </div>
    </div>
  );
}
