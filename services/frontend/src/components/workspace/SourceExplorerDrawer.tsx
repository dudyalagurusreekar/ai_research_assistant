"use client";

import { useResearchStore } from "@/stores/researchStore";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Network, Search, Upload, BookOpen } from "lucide-react";

const DEMO_SOURCES = [
  {
    id: "doc_01",
    title: "CRISPR-Cas9 vs Cas12a Specificity Study.pdf",
    type: "PDF Document",
    chunks: 42,
    similarity: 0.984,
  },
  {
    id: "doc_02",
    title: "Nature_Genetics_Off_Target_Mutations_2025.pdf",
    type: "Academic Journal",
    chunks: 88,
    similarity: 0.962,
  },
  {
    id: "doc_03",
    title: "GraphRAG_Entity_Knowledge_Base_Export.json",
    type: "Knowledge Graph",
    chunks: 156,
    similarity: 0.991,
  },
];

export function SourceExplorerDrawer({ onOpenUpload }: { onOpenUpload: () => void }) {
  const { uploadedFiles } = useResearchStore();

  return (
    <Card className="glass-panel h-full flex flex-col overflow-hidden">
      <CardHeader className="pb-3 border-b border-border/50 flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-primary" /> Source Explorer
          </CardTitle>
          <CardDescription className="text-[11px]">
            Indexed documents & pgvector hybrid evidence
          </CardDescription>
        </div>
        <button
          onClick={onOpenUpload}
          className="flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
        >
          <Upload className="h-3.5 w-3.5" /> Upload File
        </button>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto p-4 space-y-3">
        {uploadedFiles.map((file) => (
          <div
            key={file.id}
            className="rounded-lg border border-border/60 bg-secondary/30 p-2.5 space-y-1 hover:border-primary/40 transition-colors text-xs"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground truncate max-w-[180px]">{file.filename}</span>
              <Badge variant="success">READY</Badge>
            </div>
            <p className="text-[10px] text-muted-foreground">
              Size: {(file.file_size / 1024).toFixed(1)} KB • Parsed & Indexed
            </p>
          </div>
        ))}

        {DEMO_SOURCES.map((source) => (
          <div
            key={source.id}
            className="rounded-lg border border-border/60 bg-secondary/30 p-2.5 space-y-1 hover:border-primary/40 transition-colors text-xs"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground truncate max-w-[180px]">{source.title}</span>
              <Badge variant="neutral">{source.type}</Badge>
            </div>
            <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border/40">
              <span>{source.chunks} Index Chunks</span>
              <span className="font-mono text-emerald-400">{(source.similarity * 100).toFixed(1)}% Match</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
