"use client";

import React, { useState } from "react";
import { useConnectorStore } from "@/store/use-connector-store";
import { ConnectorCard } from "@/features/connectors/components/ConnectorCard";
import { ConnectorConfigDrawer } from "@/features/connectors/components/ConnectorConfigDrawer";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Link2, Search, CheckCircle2, ShieldCheck, RefreshCw } from "lucide-react";

export default function ConnectorsPage() {
  const { connectors } = useConnectorStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("ALL");

  const filtered = connectors.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = activeCategory === "ALL" || c.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const connectedCount = connectors.filter((c) => c.status === "CONNECTED").length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Link2 className="w-6 h-6 text-indigo-500" />
            Connectors Hub & Integration Center
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Unified management of PubMed, bioRxiv, openFDA, GitHub, Google Drive, Notion, and Slack integrations
          </p>
        </div>
      </div>

      {/* Integration Overview Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card variant="glass" className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-400">Connected Integrations</span>
            <h3 className="text-2xl font-bold text-slate-100">{connectedCount} Active</h3>
          </div>
        </Card>

        <Card variant="glass" className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-400">Credential Health</span>
            <h3 className="text-2xl font-bold text-emerald-400">100% Verified</h3>
          </div>
        </Card>

        <Card variant="glass" className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <RefreshCw className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-400">Total Synced Corpus</span>
            <h3 className="text-2xl font-bold text-slate-100">4,680 Items</h3>
          </div>
        </Card>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="w-full sm:w-80">
          <Input
            placeholder="Search integration connectors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {["ALL", "LITERATURE", "DEVELOPER", "CLOUD_STORAGE", "COMMUNICATION"].map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
                activeCategory === cat
                  ? "bg-indigo-600 text-white shadow-glow-indigo"
                  : "bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 border border-slate-200 dark:border-slate-800"
              }`}
            >
              {cat === "ALL" ? "All Categories" : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Connectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((c) => (
          <ConnectorCard key={c.id} connector={c} />
        ))}
      </div>

      <ConnectorConfigDrawer />
    </div>
  );
}
