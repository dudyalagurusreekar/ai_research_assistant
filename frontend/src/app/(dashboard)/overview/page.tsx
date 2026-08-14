"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SystemHealthBar } from "@/features/dashboard/components/SystemHealthBar";
import { MetricsChart } from "@/features/dashboard/components/MetricsChart";
import { ActiveWorkflows } from "@/features/dashboard/components/ActiveWorkflows";
import {
  Microscope,
  BrainCircuit,
  Network,
  FileText,
  ShieldCheck,
  Zap,
  TrendingUp,
  Clock,
  ArrowRight,
  Plus,
  BarChart,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";

export default function OverviewPage() {
  const statCards = [
    {
      title: "Research Sessions",
      value: "42",
      change: "+12% this week",
      icon: <Microscope className="w-5 h-5 text-indigo-500" />,
      badge: "Active",
      badgeVariant: "brand" as const,
    },
    {
      title: "Knowledge Nodes",
      value: "1,248",
      change: "spaCy + NetworkX graph",
      icon: <Network className="w-5 h-5 text-cyan-500" />,
      badge: "Sprint 11",
      badgeVariant: "info" as const,
    },
    {
      title: "Indexed Documents",
      value: "156",
      change: "Hybrid Vector + BM25",
      icon: <FileText className="w-5 h-5 text-emerald-500" />,
      badge: "RAG 100%",
      badgeVariant: "success" as const,
    },
    {
      title: "Release Pass Rate",
      value: "100%",
      change: "150/150 Benchmark Tasks",
      icon: <ShieldCheck className="w-5 h-5 text-amber-500" />,
      badge: "GA Approved",
      badgeVariant: "warning" as const,
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Command Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl glass-card border border-indigo-500/20 shadow-glow-indigo">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-slate-100">
              Research Command Center
            </h1>
            <Badge variant="brand">v1.0 GA</Badge>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Real-time multi-agent execution telemetry, knowledge graph synthesis, and health monitoring.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link href="/chat">
            <Button variant="primary" leftIcon={<BrainCircuit className="w-4 h-4" />}>
              Open AI Chat Workspace
            </Button>
          </Link>
          <Link href="/research">
            <Button variant="outline" leftIcon={<Plus className="w-4 h-4" />}>
              New Session
            </Button>
          </Link>
        </div>
      </div>

      {/* Real-time System Health Bar */}
      <SystemHealthBar />

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card, i) => (
          <Card key={i} variant="glass" className="hover:scale-[1.02] transition-transform">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800/80">
                {card.icon}
              </div>
              <Badge variant={card.badgeVariant}>{card.badge}</Badge>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                {card.title}
              </span>
              <h2 className="text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
                {card.value}
              </h2>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-3 pt-3 border-t border-slate-200/50 dark:border-slate-800/50 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-emerald-500" />
              <span>{card.change}</span>
            </p>
          </Card>
        ))}
      </div>

      {/* Telemetry Charts & Active Workflows */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart />
        <ActiveWorkflows />
      </div>

      {/* Release Benchmark Readiness Card */}
      <Card variant="glass">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Release Benchmark Readiness (Sprint 12 & 13)
            </CardTitle>
            <CardDescription>Final benchmark suite evaluation results across 150 tasks</CardDescription>
          </div>
          <Badge variant="success">100% PASS RATE</Badge>
        </CardHeader>

        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-[11px] font-bold text-slate-400 uppercase">RAG Recall@K</span>
            <h3 className="text-xl font-black text-emerald-400 mt-1">100.0%</h3>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Citation Accuracy</span>
            <h3 className="text-xl font-black text-cyan-400 mt-1">100.0%</h3>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Hallucination Rate</span>
            <h3 className="text-xl font-black text-indigo-400 mt-1">0.00%</h3>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Security Vulnerabilities</span>
            <h3 className="text-xl font-black text-emerald-400 mt-1">0 Found</h3>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
