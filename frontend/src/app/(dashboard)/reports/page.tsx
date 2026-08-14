"use client";

import React, { useState } from "react";
import { GeneratedReport, useReportsStore } from "@/store/use-reports-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { FileText, Download, Eye, Plus, Search, Trash2, Copy, Sparkles } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export default function ReportsPage() {
  const { reports, templates, deleteReport, addReport } = useReportsStore();
  const { addToast } = useUIStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedReport, setSelectedReport] = useState<GeneratedReport | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const filtered = reports.filter((r) => r.title.toLowerCase().includes(searchQuery.toLowerCase()) || r.summary.toLowerCase().includes(searchQuery.toLowerCase()));

  const handleExport = (report: GeneratedReport, format: "markdown" | "html") => {
    const type = format === "html" ? "text/html" : "text/markdown";
    const ext = format === "html" ? "html" : "md";
    const blob = new Blob([report.content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.title.replace(/\s+/g, "_")}.${ext}`;
    a.click();
    addToast({ type: "success", title: "Report Exported", message: `Downloaded ${report.title} as .${ext}` });
  };

  const handleDuplicate = (report: GeneratedReport) => {
    const dup: GeneratedReport = {
      ...report,
      id: `rep_${Date.now()}`,
      title: `${report.title} (Copy)`,
      created_at: new Date().toISOString(),
    };
    addReport(dup);
    addToast({ type: "info", title: "Report Duplicated", message: `Created copy of ${report.title}` });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-500" />
            Reports Center & Export Platform
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Preview, manage, duplicate, and export AI-generated research synthesis reports across formats
          </p>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="w-full sm:w-80">
          <Input
            placeholder="Search reports..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filtered.map((rep) => (
          <Card key={rep.id} variant="glass" className="hover:scale-[1.01] transition-transform flex flex-col justify-between">
            <CardHeader>
              <div className="flex items-center justify-between mb-2">
                <Badge variant={rep.status === "completed" ? "success" : "warning"}>{rep.status}</Badge>
                <span className="text-[10px] text-slate-400 font-mono">
                  {new Date(rep.created_at).toLocaleDateString()}
                </span>
              </div>
              <CardTitle className="text-base font-bold text-slate-100">{rep.title}</CardTitle>
              <CardDescription className="text-xs line-clamp-2">{rep.summary}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedReport(rep);
                      setPreviewOpen(true);
                    }}
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                  >
                    Preview
                  </Button>

                  <button
                    onClick={() => handleDuplicate(rep)}
                    className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                    title="Duplicate Report"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => {
                      deleteReport(rep.id);
                      addToast({ type: "info", title: "Report Deleted", message: rep.title });
                    }}
                    className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
                    title="Delete Report"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleExport(rep, "markdown")}
                  leftIcon={<Download className="w-3.5 h-3.5" />}
                >
                  Export .MD
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Report Templates Section */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            Saved Report Templates
          </CardTitle>
          <CardDescription>Structured outlines for automated synthesis generation</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {templates.map((tpl) => (
            <div key={tpl.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <h4 className="text-xs font-bold text-slate-100">{tpl.name}</h4>
              <p className="text-xs text-slate-400 leading-relaxed">{tpl.description}</p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {tpl.structure_outline.map((step, idx) => (
                  <Badge key={idx} variant="brand" size="sm">
                    {step}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Preview Modal */}
      <Modal isOpen={previewOpen} onClose={() => setPreviewOpen(false)} title={selectedReport?.title || "Report Preview"} className="max-w-3xl">
        {selectedReport && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-950 font-mono text-xs text-slate-200 leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto border border-slate-800">
              {selectedReport.content}
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <Button variant="outline" onClick={() => handleExport(selectedReport, "html")}>
                Export HTML
              </Button>
              <Button variant="primary" onClick={() => handleExport(selectedReport, "markdown")} leftIcon={<Download className="w-4 h-4" />}>
                Export Markdown
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
