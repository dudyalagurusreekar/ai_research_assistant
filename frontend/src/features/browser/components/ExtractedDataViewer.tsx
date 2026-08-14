"use client";

import React from "react";
import { useBrowserStore } from "@/store/use-browser-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Download, Code, Image as ImageIcon } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function ExtractedDataViewer() {
  const { extractedData, screenshots } = useBrowserStore();
  const { addToast } = useUIStore();

  const handleExportJSON = (title: string, data: any) => {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/\s+/g, "_")}.json`;
    a.click();
    addToast({ type: "success", title: "JSON Exported", message: "Downloaded extracted JSON dataset." });
  };

  return (
    <div className="space-y-6">
      {/* Extracted JSON Data */}
      <Card variant="glass">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Code className="w-5 h-5 text-indigo-400" />
              Extracted Structured JSON Datasets ({extractedData.length})
            </CardTitle>
            <CardDescription>Structured entity tables extracted from Playwright sessions</CardDescription>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {extractedData.map((item) => (
            <div key={item.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-100">{item.title}</h4>
                  <span className="text-[10px] text-slate-400 font-mono">{item.url}</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExportJSON(item.title, item.data)}
                  leftIcon={<Download className="w-3.5 h-3.5" />}
                >
                  Export JSON
                </Button>
              </div>

              <pre className="p-3 rounded-lg bg-slate-950 font-mono text-xs text-indigo-300 overflow-x-auto border border-slate-800/80">
                {JSON.stringify(item.data, null, 2)}
              </pre>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Screenshots Gallery */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-cyan-400" />
            Captured Screenshots Gallery
          </CardTitle>
          <CardDescription>Playwright viewport screenshots saved to object storage</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {screenshots.map((scr) => (
            <div key={scr.id} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-slate-200">
                <span>{scr.title}</span>
                <Badge variant="info">Viewport</Badge>
              </div>
              <div className="h-40 rounded-lg bg-slate-950 overflow-hidden relative border border-slate-800 flex items-center justify-center">
                <img src={scr.url} alt={scr.title} className="w-full h-full object-cover" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
