"use client";

import React, { useState } from "react";
import { MetricSeries } from "../services/dashboard-service";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Activity, Zap, ShieldCheck } from "lucide-react";

export function MetricsChart({ data }: { data?: MetricSeries[] }) {
  const [metricType, setMetricType] = useState<"tokens" | "latency" | "groundedness">("tokens");

  const sampleData = data || [
    { timestamp: "00:00", tokens: 1200, latency_ms: 110, groundedness: 0.96 },
    { timestamp: "04:00", tokens: 2400, latency_ms: 95, groundedness: 0.98 },
    { timestamp: "08:00", tokens: 4800, latency_ms: 125, groundedness: 0.97 },
    { timestamp: "12:00", tokens: 8900, latency_ms: 105, groundedness: 0.99 },
    { timestamp: "16:00", tokens: 6200, latency_ms: 98, groundedness: 0.98 },
    { timestamp: "20:00", tokens: 9400, latency_ms: 115, groundedness: 0.99 },
  ];

  const getValues = () => {
    if (metricType === "tokens") return sampleData.map((d) => d.tokens);
    if (metricType === "latency") return sampleData.map((d) => d.latency_ms);
    return sampleData.map((d) => d.groundedness * 100);
  };

  const values = getValues();
  const maxVal = Math.max(...values, 1);
  const minVal = Math.min(...values, 0);

  // Generate SVG path points
  const points = values.map((val, idx) => {
    const x = (idx / (values.length - 1)) * 400;
    const y = 150 - ((val - minVal) / (maxVal - minVal || 1)) * 120;
    return `${x},${y}`;
  }).join(" ");

  return (
    <Card variant="glass">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            AI Orchestration & Performance Telemetry
          </CardTitle>
          <CardDescription>Real-time metrics from Prometheus & OpenTelemetry</CardDescription>
        </div>

        {/* Metric Selector Pills */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setMetricType("tokens")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
              metricType === "tokens" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Tokens
          </button>
          <button
            onClick={() => setMetricType("latency")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
              metricType === "latency" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Latency
          </button>
          <button
            onClick={() => setMetricType("groundedness")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
              metricType === "groundedness" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Groundedness
          </button>
        </div>
      </CardHeader>

      <CardContent>
        {/* SVG Sparkline / Area Chart */}
        <div className="h-44 w-full relative pt-2">
          <svg viewBox="0 0 400 160" className="w-full h-full overflow-visible">
            <defs>
              <linearGradient id="metricGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid Lines */}
            <line x1="0" y1="30" x2="400" y2="30" stroke="#334155" strokeDasharray="3 3" strokeOpacity="0.3" />
            <line x1="0" y1="80" x2="400" y2="80" stroke="#334155" strokeDasharray="3 3" strokeOpacity="0.3" />
            <line x1="0" y1="130" x2="400" y2="130" stroke="#334155" strokeDasharray="3 3" strokeOpacity="0.3" />

            {/* Filled Gradient Area */}
            <polygon points={`0,160 ${points} 400,160`} fill="url(#metricGrad)" />

            {/* Metric Polyline */}
            <polyline fill="none" stroke="#818cf8" strokeWidth="3" points={points} />

            {/* Data Points */}
            {values.map((val, idx) => {
              const x = (idx / (values.length - 1)) * 400;
              const y = 150 - ((val - minVal) / (maxVal - minVal || 1)) * 120;
              return (
                <circle
                  key={idx}
                  cx={x}
                  cy={y}
                  r="4"
                  className="fill-indigo-400 stroke-slate-950 stroke-2 hover:r-6 transition-all"
                />
              );
            })}
          </svg>
        </div>

        {/* X-Axis Timestamps */}
        <div className="flex justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800">
          {sampleData.map((d, i) => (
            <span key={i}>{d.timestamp}</span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
