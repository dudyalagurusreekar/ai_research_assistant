"use client";

import React from "react";
import { useDataStore } from "@/store/use-data-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { BarChart3, LineChart, PieChart, ScatterChart, Download } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function DataVisualizationStudio() {
  const { datasets, chartType, setChartType, xAxisColumn, setXAxisColumn, yAxisColumn, setYAxisColumn } =
    useDataStore();
  const dataset = datasets[0];

  const sampleData = dataset.sample_rows;

  return (
    <Card variant="glass" className="space-y-4">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            Interactive Visualization Studio
          </CardTitle>
          <CardDescription>Render high-dimensional charts with dynamic axis mapping</CardDescription>
        </div>

        {/* Chart Type Selector */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setChartType("bar")}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
              chartType === "bar" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" /> Bar
          </button>
          <button
            onClick={() => setChartType("line")}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
              chartType === "line" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <LineChart className="w-3.5 h-3.5" /> Line
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Axes Config Toolbar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">X-Axis Column</label>
            <select
              value={xAxisColumn}
              onChange={(e) => setXAxisColumn(e.target.value)}
              className="w-full text-xs font-semibold p-2 rounded-lg bg-slate-950 text-slate-100 border border-slate-800"
            >
              {dataset.columns.map((col) => (
                <option key={col.name} value={col.name}>{col.name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Y-Axis Column</label>
            <select
              value={yAxisColumn}
              onChange={(e) => setYAxisColumn(e.target.value)}
              className="w-full text-xs font-semibold p-2 rounded-lg bg-slate-950 text-slate-100 border border-slate-800"
            >
              {dataset.columns.map((col) => (
                <option key={col.name} value={col.name}>{col.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Dynamic Chart Canvas Render */}
        <div className="h-64 rounded-xl bg-slate-950 border border-slate-800 p-6 flex flex-col justify-end relative overflow-hidden">
          <div className="absolute top-4 left-4 text-xs font-mono text-slate-400">
            Plotting: <span className="text-indigo-400 font-bold">{yAxisColumn}</span> vs <span className="text-cyan-400 font-bold">{xAxisColumn}</span>
          </div>

          {/* Render Bars */}
          <div className="flex items-end justify-around h-44 w-full gap-4 pt-6">
            {sampleData.map((row, idx) => {
              const val = Number(row[yAxisColumn] || 0.05) * 100;
              const heightPct = Math.min(Math.max(val * 2, 15), 100);
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2 group">
                  <div
                    className="w-full bg-gradient-to-t from-indigo-600 to-cyan-400 rounded-t-lg transition-all duration-300 group-hover:brightness-125"
                    style={{ height: `${heightPct}%` }}
                  />
                  <span className="text-[10px] font-mono text-slate-400 truncate max-w-full">
                    {String(row[xAxisColumn] || `Item ${idx}`)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
