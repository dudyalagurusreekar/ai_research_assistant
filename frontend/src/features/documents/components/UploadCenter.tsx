"use client";

import React, { useState, useRef } from "react";
import { useDocumentStore } from "@/store/use-document-store";
import { useUIStore } from "@/store/use-ui-store";
import { documentService } from "../services/document-service";
import { UploadCloud, File, CheckCircle2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export function UploadCenter() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addDocument } = useDocumentStore();
  const { addToast } = useUIStore();

  const [isUploading, setIsUploading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState<string | null>(null);

  const handleFiles = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    setIsUploading(true);
    setPipelineStep("Step 1: Multi-Modal PDF Extraction");

    setTimeout(async () => {
      setPipelineStep("Step 2: Recursive Text Chunking & Tokenization");
      setTimeout(async () => {
        setPipelineStep("Step 3: 1,536-dim Vector Embedding Generation");
        setTimeout(async () => {
          setPipelineStep("Step 4: PostgreSQL + pgvector Indexing & MinIO Sync");
          const newDoc = await documentService.uploadDocument(file);
          addDocument(newDoc);
          addToast({ type: "success", title: "Document Indexed", message: `${file.name} chunked into pgvector.` });
          setIsUploading(false);
          setPipelineStep(null);
        }, 600);
      }, 600);
    }, 600);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      className="glass-card rounded-2xl p-6 border-2 border-dashed border-indigo-500/30 hover:border-indigo-500/60 cursor-pointer transition-all text-center space-y-3 shadow-glow-indigo group"
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.csv,.json"
        onChange={(e) => e.target.files && handleFiles(e.target.files)}
        className="hidden"
      />

      <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
        <UploadCloud className="w-6 h-6" />
      </div>

      <div className="space-y-1">
        <h4 className="text-sm font-bold text-slate-100">
          Upload PDF Literature or Research Datasets
        </h4>
        <p className="text-xs text-slate-400">
          Drag & drop files or click to browse. Automatically extracts entities, chunks text, and generates 1536-dim embeddings.
        </p>
      </div>

      {isUploading && pipelineStep && (
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-2 animate-fade-in">
          <div className="flex items-center justify-between text-indigo-400 font-semibold">
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 animate-spin" />
              {pipelineStep}
            </span>
            <Badge variant="brand">Processing</Badge>
          </div>
          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-500 animate-pulse rounded-full w-3/4" />
          </div>
        </div>
      )}
    </div>
  );
}
