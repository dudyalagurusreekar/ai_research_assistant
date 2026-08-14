"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FlaskConical,
  Network,
  Scale,
  FileText,
  Plus,
  ArrowRight,
  TrendingUp,
  Cpu,
  CheckCircle2,
  Clock,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

const METRICS = [
  { label: "Active Research Tasks", value: "14", change: "+12% this week", icon: FlaskConical, color: "text-sky-400" },
  { label: "GraphRAG Entity Nodes", value: "48,290", change: "99.4% confidence", icon: Network, color: "text-purple-400" },
  { label: "Decision Trade-off Analyses", value: "128", change: "Pareto optimal", icon: Scale, color: "text-emerald-400" },
  { label: "Indexed Documents", value: "1,420", change: "pgvector hybrid", icon: FileText, color: "text-amber-400" },
];

const RECENT_TASKS = [
  {
    id: "task_01",
    title: "Synthesize CRISPR Off-Target Gene Editing Literature",
    status: "RUNNING",
    progress: "Step 7/12",
    updated: "10 mins ago",
    confidence: 0.964,
  },
  {
    id: "task_02",
    title: "Quantum Error Correction Threshold Analysis",
    status: "COMPLETED",
    progress: "12/12 Steps",
    updated: "1 hour ago",
    confidence: 0.991,
  },
  {
    id: "task_03",
    title: "MCDA Trade-Off Model for Battery Chemistry Selection",
    status: "COMPLETED",
    progress: "8/8 Steps",
    updated: "3 hours ago",
    confidence: 0.985,
  },
  {
    id: "task_04",
    title: "Headless Web Scraping of FDA Drug Recall Notices",
    status: "RUNNING",
    progress: "Step 3/5",
    updated: " Just now",
    confidence: 0.942,
  },
];

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Welcome Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Research Control Center <Sparkles className="h-5 w-5 text-primary" />
            </h1>
            <p className="text-sm text-muted-foreground">
              Autonomous multi-agent orchestration, GraphRAG memory, and decision intelligence.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/workspace">
              <Button className="gap-2">
                <Plus className="h-4 w-4" /> New Autonomous Task
              </Button>
            </Link>
          </div>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {METRICS.map((metric) => {
            const Icon = metric.icon;
            return (
              <Card key={metric.label} className="glass-panel hover:border-primary/50 transition-all">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-xs font-semibold text-muted-foreground">{metric.label}</CardTitle>
                  <Icon className={`h-5 w-5 ${metric.color}`} />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold tracking-tight text-foreground">{metric.value}</div>
                  <p className="text-[11px] text-muted-foreground flex items-center gap-1 mt-1">
                    <TrendingUp className="h-3 w-3 text-emerald-400" /> {metric.change}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Dashboard Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Research Task Stream */}
          <Card className="lg:col-span-2 glass-panel">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <div>
                <CardTitle className="text-base">Active Research Workflows</CardTitle>
                <CardDescription className="text-xs">
                  Real-time status of multi-step task DAGs across LLM providers
                </CardDescription>
              </div>
              <Link href="/workspace">
                <Button variant="ghost" size="sm" className="text-xs gap-1">
                  View All <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {RECENT_TASKS.map((task) => (
                <div
                  key={task.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-lg border border-border/60 bg-secondary/20 p-3.5 hover:bg-secondary/40 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-foreground">{task.title}</span>
                      <Badge variant={task.status === "COMPLETED" ? "success" : "running"}>
                        {task.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {task.updated}</span>
                      <span>Progress: {task.progress}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span className="text-xs font-mono font-semibold text-emerald-400">{(task.confidence * 100).toFixed(1)}%</span>
                      <p className="text-[10px] text-muted-foreground">Confidence</p>
                    </div>
                    <Link href={`/workspace?task_id=${task.id}`}>
                      <Button variant="outline" size="sm" className="text-xs">
                        Open DAG
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* System Health & Provider Telemetry Panel */}
          <div className="space-y-6">
            <Card className="glass-panel">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-primary" /> Orchestration Telemetry
                </CardTitle>
                <CardDescription className="text-xs">Multi-provider routing & token cache</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <span className="text-muted-foreground">Active Model Route</span>
                  <span className="font-semibold text-foreground">Gemini 2.5 Pro / Flash</span>
                </div>
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <span className="text-muted-foreground">Response Cache Hit Rate</span>
                  <span className="font-semibold text-emerald-400">94.2%</span>
                </div>
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <span className="text-muted-foreground">Vector Index Storage</span>
                  <span className="font-semibold text-foreground">pgvector HNSW</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Circuit Breaker Status</span>
                  <span className="flex items-center gap-1 font-semibold text-emerald-400">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Healthy
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="glass-panel bg-primary/5 border-primary/20">
              <CardHeader>
                <CardTitle className="text-base text-primary">Sprint 14 Quality Gate</CardTitle>
                <CardDescription className="text-xs">Enterprise Evaluation Suite</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-xs text-muted-foreground">
                  Continuous benchmark evaluation is active across 2,600 test scenarios.
                </p>
                <div className="flex items-center justify-between text-xs font-semibold pt-2">
                  <span>Pass Rate:</span>
                  <span className="text-emerald-400">100% (98/98 verified)</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
