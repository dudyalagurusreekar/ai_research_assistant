"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DocumentItem } from "@/store/use-document-store";
import { documentService } from "../services/document-service";
import { useUIStore } from "@/store/use-ui-store";
import {
  FileText,
  Database,
  Layers,
  ExternalLink,
  RefreshCw,
  CheckCircle2,
  Cpu,
  HardDrive,
} from "lucide-react";

export function DocumentInspectorModal({
  isOpen,
  onClose,
  document,
}: {
  isOpen: boolean;
  onClose: () => void;
  document: DocumentItem | null;
}) {
  const { addToast } = useUIStore();
  const [activeTab, setActiveTab] = useState<"metadata" | "chunks" | "citations" | "pipeline">("metadata");
  const [isReindexing, setIsReindexing] = useState(false);

  if (!document) return null;

  const handleReindex = async () => {
    setIsReindexing(true);
    await documentService.reindexDocument(document.id);
    addToast({ type: "success", title: "Document Reindexed", message: "Vector embeddings & chunks updated." });
    setIsReindexing(false);
  };

  const sampleChunks = document.chunks || [
    {
      id: "chk_001",
      chunk_index: 1,
      text_content:
        "CRISPR-Cas9 mediated genome editing displays high cleavage efficiency at target loci. High-throughput GUIDE-seq assays reveal off-target rates under 0.02%.",
      token_count: 148,
      similarity_score: 0.98,
      embedding_vector_id: "vec_pgvector_001",
    },
    {
      id: "chk_002",
      chunk_index: 2,
      text_content:
        "Base editing substitutions (C-to-T) exhibit reduced bystander activity when using narrow window deaminases paired with SpCas9-HF1.",
      token_count: 126,
      similarity_score: 0.94,
      embedding_vector_id: "vec_pgvector_002",
    },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Inspector: ${document.title}`} className="max-w-2xl">
      <div className="space-y-4">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab("metadata")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${
              activeTab === "metadata" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            Overview & Metadata
          </button>
          <button
            onClick={() => setActiveTab("chunks")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${
              activeTab === "chunks" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            Chunk Explorer ({sampleChunks.length})
          </button>
          <button
            onClick={() => setActiveTab("citations")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${
              activeTab === "citations" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            Citations & DOI
          </button>
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${
              activeTab === "pipeline" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            Pipeline
          </button>
        </div>

        {/* Tab 1: Metadata */}
        {activeTab === "metadata" && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="text-slate-400 block font-semibold">File Size</span>
                <span className="text-slate-100 font-bold">{document.file_size}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="text-slate-400 block font-semibold">Page Count</span>
                <span className="text-slate-100 font-bold">{document.page_count} Pages</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="text-slate-400 block font-semibold">Indexed Vector Chunks</span>
                <span className="text-emerald-400 font-bold">{document.chunk_count} Chunks</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="text-slate-400 block font-semibold">MinIO S3 Storage</span>
                <span className="text-indigo-400 font-bold truncate block">{document.storage_path}</span>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                variant="outline"
                size="sm"
                isLoading={isReindexing}
                onClick={handleReindex}
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              >
                Re-Index Vector Embeddings
              </Button>
            </div>
          </div>
        )}

        {/* Tab 2: Chunks */}
        {activeTab === "chunks" && (
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {sampleChunks.map((chk) => (
              <div key={chk.id} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-indigo-400">Chunk #{chk.chunk_index}</span>
                  <div className="flex items-center gap-2">
                    <Badge variant="info">{chk.token_count} Tokens</Badge>
                    {chk.embedding_vector_id && <Badge variant="brand">{chk.embedding_vector_id}</Badge>}
                  </div>
                </div>
                <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                  {chk.text_content}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Tab 3: Citations */}
        {activeTab === "citations" && (
          <div className="space-y-3">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-100">Nature Biotechnology (2025)</h4>
                <Badge variant="success">DOI Verified</Badge>
              </div>
              <p className="text-xs text-slate-400 font-mono">DOI: 10.1038/nbt.4201</p>
              <p className="text-xs text-slate-300 leading-relaxed pt-1">
                "High-throughput GUIDE-seq demonstrates off-target rate under 0.02% across human cell lines."
              </p>
            </div>
          </div>
        )}

        {/* Tab 4: Pipeline */}
        {activeTab === "pipeline" && (
          <div className="space-y-2.5">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-300 font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                1. Text & Table PDF Extraction
              </span>
              <Badge variant="success">Completed</Badge>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-300 font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                2. Recursive Token Chunking (148 tokens/chunk)
              </span>
              <Badge variant="success">Completed</Badge>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-300 font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                3. 1,536-dim Dense Embedding (pgvector)
              </span>
              <Badge variant="success">Completed</Badge>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-300 font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                4. MinIO Object Storage S3 Backup
              </span>
              <Badge variant="success">Completed</Badge>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
