"use client";

import React from "react";
import { DatasetProfile } from "@/store/use-data-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Database, Table, AlertTriangle, CheckCircle2 } from "lucide-react";

export function DatasetProfiler({ dataset }: { dataset: DatasetProfile }) {
  return (
    <div className="space-y-6">
      {/* Metric Cards Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card variant="glass">
          <span className="text-xs font-semibold text-slate-400">Total Rows</span>
          <h3 className="text-2xl font-black text-slate-100 mt-1">{dataset.row_count.toLocaleString()}</h3>
        </Card>
        <Card variant="glass">
          <span className="text-xs font-semibold text-slate-400">Total Columns</span>
          <h3 className="text-2xl font-black text-slate-100 mt-1">{dataset.column_count}</h3>
        </Card>

        <Card variant="glass">
          <span className="text-xs font-semibold text-slate-400">File Size</span>
          <h3 className="text-2xl font-black text-slate-100 mt-1">{dataset.file_size}</h3>
        </Card>

        <Card variant="glass">
          <span className="text-xs font-semibold text-slate-400">Anomalies Detected</span>
          <h3 className="text-2xl font-black text-amber-400 mt-1 flex items-center gap-1.5">
            {dataset.anomalies_detected} Outliers
          </h3>
        </Card>
      </div>

      {/* Column Schema Profiling Table */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Table className="w-5 h-5 text-indigo-400" />
            Column Schema & Statistical Profiling
          </CardTitle>
          <CardDescription>Automated type inference, missing value analysis, and summary metrics</CardDescription>
        </CardHeader>

        <CardContent>
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Column Name</th>
                  <th className="px-4 py-3">Inferred Type</th>
                  <th className="px-4 py-3">Missing %</th>
                  <th className="px-4 py-3">Unique Values</th>
                  <th className="px-4 py-3">Mean ± Std</th>
                  <th className="px-4 py-3">[Min, Max]</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {dataset.columns.map((col, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40">
                    <td className="px-4 py-3 font-bold text-slate-100">{col.name}</td>
                    <td className="px-4 py-3">
                      <Badge variant={col.data_type === "numeric" ? "brand" : "info"}>{col.data_type}</Badge>
                    </td>
                    <td className="px-4 py-3 font-mono text-emerald-400">{col.null_percentage}%</td>
                    <td className="px-4 py-3 font-mono">{col.unique_count}</td>
                    <td className="px-4 py-3 font-mono">
                      {col.mean !== undefined ? `${col.mean.toFixed(3)} ± ${col.std?.toFixed(3)}` : "N/A"}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-400">
                      {col.min !== undefined ? `[${col.min}, ${col.max}]` : "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
