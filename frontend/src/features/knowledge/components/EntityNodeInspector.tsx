"use client";

import React from "react";
import { useKnowledgeStore } from "@/store/use-knowledge-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Shield, Eye, ShieldAlert, Cpu, CheckCircle2 } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function EntityNodeInspector() {
  const { selectedNode, setSelectedNode } = useKnowledgeStore();
  const { addToast } = useUIStore();

  if (!selectedNode) {
    return (
      <Card variant="glass" className="p-6 text-center text-slate-400 text-xs">
        Click on any node in the graph topology canvas to inspect entity properties and provenance.
      </Card>
    );
  }

  const handleRedact = () => {
    addToast({ type: "info", title: "PII Redaction Applied", message: `Redacted entity "${selectedNode.name}".` });
  };

  return (
    <Card variant="glass" className="space-y-4">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            {selectedNode.name}
          </CardTitle>
          <CardDescription>Entity Type: {selectedNode.type}</CardDescription>
        </div>
        <Badge variant="brand">{selectedNode.sensitivity}</Badge>
      </CardHeader>

      <CardContent className="space-y-4 text-xs">
        <p className="text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          {selectedNode.description}
        </p>

        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-slate-400 block font-semibold">PageRank Centrality</span>
            <span className="text-indigo-400 font-bold text-base">{selectedNode.pagerank_score}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-slate-400 block font-semibold">Degree Centrality</span>
            <span className="text-cyan-400 font-bold text-base">{selectedNode.degree} Edges</span>
          </div>
        </div>

        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="space-y-0.5">
            <span className="font-bold text-slate-200">PII Redaction Status</span>
            <p className="text-[10px] text-slate-400">Sprint 11 Privacy Engine</p>
          </div>
          <Badge variant="success">{selectedNode.pii_status}</Badge>
        </div>

        <div className="flex gap-2 pt-2">
          <Button variant="outline" size="sm" className="flex-1" onClick={handleRedact} leftIcon={<Shield className="w-3.5 h-3.5" />}>
            Apply PII Redaction
          </Button>
          <Button variant="danger" size="sm" className="flex-1" leftIcon={<ShieldAlert className="w-3.5 h-3.5" />}>
            Purge Subgraph
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
