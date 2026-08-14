"use client";

import React, { useState } from "react";
import { WorkflowItem } from "../services/dashboard-service";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Play, Pause, RefreshCw, Cpu, BrainCircuit, CheckCircle2 } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function ActiveWorkflows({ workflows }: { workflows?: WorkflowItem[] }) {
  const { addToast } = useUIStore();

  const initialWorkflows: WorkflowItem[] = workflows || [
    {
      id: "wf_001",
      title: "CRISPR-Cas9 Base Editor Off-Target Specificity",
      status: "running",
      progress: 75,
      current_step: "NetworkX Graph Centrality Audit",
      nodes_extracted: 42,
      started_at: new Date().toISOString(),
    },
    {
      id: "wf_002",
      title: "AlphaFold 3 Multimer Structure Prediction",
      status: "paused",
      progress: 40,
      current_step: "PDB Coordinate Similarity Search",
      nodes_extracted: 18,
      started_at: new Date().toISOString(),
    },
  ];

  const [items, setItems] = useState<WorkflowItem[]>(initialWorkflows);

  const handleToggleStatus = (id: string) => {
    setItems((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          const nextStatus = item.status === "running" ? "paused" : "running";
          addToast({
            type: "info",
            title: `Workflow ${nextStatus === "running" ? "Resumed" : "Paused"}`,
            message: `Supervisory execution DAG ${nextStatus}.`,
          });
          return { ...item, status: nextStatus };
        }
        return item;
      })
    );
  };

  return (
    <Card variant="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-cyan-400" />
          Active Multi-Agent Workflows
        </CardTitle>
        <CardDescription>Live supervisory planner DAG execution tasks</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {items.map((wf) => (
          <div
            key={wf.id}
            className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h4 className="text-sm font-bold text-slate-100">{wf.title}</h4>
                <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                  <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Current Step: {wf.current_step}</span>
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant={wf.status === "running" ? "brand" : wf.status === "completed" ? "success" : "warning"}>
                  {wf.status}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleToggleStatus(wf.id)}
                  leftIcon={wf.status === "running" ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                >
                  {wf.status === "running" ? "Pause" : "Resume"}
                </Button>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-semibold text-slate-400">
                <span>Execution Progress</span>
                <span className="font-mono text-cyan-400">{wf.progress}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-500 rounded-full"
                  style={{ width: `${wf.progress}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
