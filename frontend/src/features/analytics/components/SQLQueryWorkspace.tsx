"use client";

import React, { useState } from "react";
import { useDataStore } from "@/store/use-data-store";
import { dataService } from "../services/data-service";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Code, Play, Database, Clock } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function SQLQueryWorkspace() {
  const { sqlQuery, setSqlQuery, queryResult, setQueryResult } = useDataStore();
  const { addToast } = useUIStore();
  const [isExecuting, setIsExecuting] = useState(false);

  const handleRunQuery = async () => {
    if (!sqlQuery.trim()) return;
    setIsExecuting(true);
    const result = await dataService.executeSqlQuery(sqlQuery);
    setQueryResult(result);
    setIsExecuting(false);
    addToast({ type: "success", title: "Query Executed", message: `Fetched ${result.rows.length} rows in ${result.execution_time_ms}ms` });
  };

  return (
    <Card variant="glass" className="space-y-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Code className="w-5 h-5 text-indigo-400" />
          In-Memory DuckDB SQL Editor
        </CardTitle>
        <CardDescription>Run SQL queries directly over loaded data frames</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="space-y-2">
          <textarea
            rows={4}
            value={sqlQuery}
            onChange={(e) => setSqlQuery(e.target.value)}
            className="w-full font-mono text-xs p-4 rounded-xl bg-slate-950 text-indigo-300 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
            <Clock className="w-3.5 h-3.5" /> Execution Latency: {queryResult?.execution_time_ms || 18}ms
          </span>

          <Button
            variant="primary"
            isLoading={isExecuting}
            onClick={handleRunQuery}
            leftIcon={<Play className="w-4 h-4 fill-current" />}
          >
            Execute SQL
          </Button>
        </div>

        {/* Results Table */}
        {queryResult && (
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  {queryResult.columns.map((col) => (
                    <th key={col} className="px-4 py-3">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200 font-mono">
                {queryResult.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40">
                    {queryResult.columns.map((col) => (
                      <td key={col} className="px-4 py-3">
                        {String(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
