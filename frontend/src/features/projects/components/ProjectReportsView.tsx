"use client";

import React from "react";
import { useProjectStore } from "@/store/use-project-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Download, FileText, Sparkles, Share2 } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function ProjectReportsView({ projectId }: { projectId: string }) {
  const { reports } = useProjectStore();
  const { addToast } = useUIStore();

  const projectReports = reports.filter((r) => r.project_id === projectId);

  const handleExport = (reportTitle: string, content: string) => {
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${reportTitle.replace(/\s+/g, "_")}.md`;
    a.click();
    addToast({ type: "success", title: "Report Exported", message: "Downloaded Markdown report." });
  };

  return (
    <div className="space-y-4">
      {projectReports.map((rep) => (
        <Card key={rep.id} variant="glass">
          <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                {rep.title}
              </CardTitle>
              <CardDescription>{rep.summary}</CardDescription>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport(rep.title, rep.content)}
              leftIcon={<Download className="w-4 h-4" />}
            >
              Export Markdown
            </Button>
          </CardHeader>

          <CardContent>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono text-slate-300 leading-relaxed whitespace-pre-wrap max-h-80 overflow-y-auto">
              {rep.content}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
