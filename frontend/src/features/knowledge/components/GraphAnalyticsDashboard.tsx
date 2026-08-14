"use client";

import React from "react";
import { useKnowledgeStore } from "@/store/use-knowledge-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { BarChart3, Network, GitBranch, ShieldCheck } from "lucide-react";

export function GraphAnalyticsDashboard() {
  const { nodes } = useKnowledgeStore();

  const sortedNodes = [...nodes].sort((a, b) => b.pagerank_score - a.pagerank_score);

  const snapshots = [
    { version: "v1.4", date: "Today, 18:20", nodes: 1248, edges: 3840, status: "Active" },
    { version: "v1.3", date: "Yesterday, 14:00", nodes: 1180, edges: 3600, status: "Archived" },
    { version: "v1.2", date: "2 days ago", nodes: 940, edges: 2800, status: "Archived" },
  ];

  return (
    <div className="space-y-6">
      {/* Centrality Leaderboard */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            NetworkX Centrality Analytics & PageRank Leaderboard
          </CardTitle>
          <CardDescription>Top influential entities ranked by PageRank & degree centrality</CardDescription>
        </CardHeader>

        <CardContent>
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Rank</th>
                  <th className="px-4 py-3">Entity Name</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">PageRank Score</th>
                  <th className="px-4 py-3">Degree</th>
                  <th className="px-4 py-3">Evidence Count</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200 font-mono">
                {sortedNodes.map((node, idx) => (
                  <tr key={node.id} className="hover:bg-slate-900/40">
                    <td className="px-4 py-3 font-bold text-indigo-400">#{idx + 1}</td>
                    <td className="px-4 py-3 font-bold text-slate-100">{node.name}</td>
                    <td className="px-4 py-3">
                      <Badge variant="brand">{node.type}</Badge>
                    </td>
                    <td className="px-4 py-3 text-emerald-400 font-bold">{node.pagerank_score}</td>
                    <td className="px-4 py-3">{node.degree}</td>
                    <td className="px-4 py-3 text-cyan-400">{node.evidence_count} papers</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Snapshot Version History */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-cyan-400" />
            Graph Snapshot Version History
          </CardTitle>
          <CardDescription>Sprint 11 versioning and graph snapshot rollback</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {snapshots.map((snap) => (
            <div
              key={snap.version}
              className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-100">{snap.version}</span>
                  <Badge variant={snap.status === "Active" ? "success" : "neutral"}>{snap.status}</Badge>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  {snap.date} • {snap.nodes} Nodes • {snap.edges} Edges
                </p>
              </div>

              <Badge variant="info">Snapshot Intact</Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
