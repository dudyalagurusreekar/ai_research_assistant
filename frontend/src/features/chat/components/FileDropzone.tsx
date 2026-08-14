"use client";

import React, { useRef } from "react";
import { UploadCloud, File, X } from "lucide-react";
import { useChatStore } from "@/store/use-chat-store";
import { cn } from "@/lib/utils";

export function FileDropzone() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { attachedFiles, attachFiles, removeAttachedFile } = useChatStore();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      attachFiles(Array.from(e.target.files));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      attachFiles(Array.from(e.dataTransfer.files));
    }
  };

  return (
    <div className="space-y-2">
      {/* Attached Files List */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 px-1 pb-1">
          {attachedFiles.map((file, idx) => (
            <div
              key={idx}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-mono"
            >
              <File className="w-3.5 h-3.5" />
              <span className="max-w-[150px] truncate">{file.name}</span>
              <button
                type="button"
                onClick={() => removeAttachedFile(idx)}
                className="hover:text-rose-400 p-0.5 rounded transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.txt,.csv,.json,.md"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
