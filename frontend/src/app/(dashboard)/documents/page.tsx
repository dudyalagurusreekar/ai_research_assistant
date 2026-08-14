"use client";

import React, { useState } from "react";
import { useDocumentStore, DocumentItem } from "@/store/use-document-store";
import { UploadCenter } from "@/features/documents/components/UploadCenter";
import { SemanticSearchPanel } from "@/features/documents/components/SemanticSearchPanel";
import { DocumentInspectorModal } from "@/features/documents/components/DocumentInspectorModal";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { FileText, Search, Database, HardDrive, Eye, Trash2, CheckCircle2 } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export default function DocumentsPage() {
  const { documents, removeDocument, setSelectedDocument, setInspectorOpen, inspectorOpen, selectedDocument } =
    useDocumentStore();
  const { addToast } = useUIStore();
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = documents.filter((d) => d.title.toLowerCase().includes(searchQuery.toLowerCase()));

  const handleInspect = (doc: DocumentItem) => {
    setSelectedDocument(doc);
    setInspectorOpen(true);
  };

  const handleDelete = (id: string, title: string) => {
    removeDocument(id);
    addToast({ type: "info", title: "Document Removed", message: `${title} deleted from index.` });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-emerald-500" />
            Document Intelligence Center
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Multi-modal PDF ingestion, 1,536-dim vector embedding, MinIO object storage, and RAG chunk inspection
          </p>
        </div>
      </div>

      {/* Upload Box */}
      <UploadCenter />

      {/* RAG Semantic Search Engine */}
      <SemanticSearchPanel />

      {/* Document Library Grid */}
      <Card variant="glass">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle>Ingested Knowledge Corpus ({documents.length})</CardTitle>
            <CardDescription>Inspect vector chunks, citations, and MinIO storage paths</CardDescription>
          </div>
          <div className="w-full sm:w-72">
            <Input
              placeholder="Search document corpus..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {filtered.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-500">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-100">{doc.title}</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {doc.file_size} • {doc.page_count} pages • {doc.chunk_count} vector chunks
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="success">{doc.status}</Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleInspect(doc)}
                  leftIcon={<Eye className="w-3.5 h-3.5" />}
                >
                  Inspect
                </Button>
                <button
                  onClick={() => handleDelete(doc.id, doc.title)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 transition-colors"
                  title="Delete Document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Inspector Modal */}
      <DocumentInspectorModal
        isOpen={inspectorOpen}
        onClose={() => setInspectorOpen(false)}
        document={selectedDocument}
      />
    </div>
  );
}
