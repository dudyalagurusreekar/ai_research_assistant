"use client";

import React, { useState } from "react";
import { useProjectStore } from "@/store/use-project-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Save, Eye, FileText, CheckCircle2 } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function ProjectNotesEditor({ projectId }: { projectId: string }) {
  const { notes, saveNote } = useProjectStore();
  const { addToast } = useUIStore();

  const existingNote = notes.find((n) => n.project_id === projectId) || {
    id: `note_${Date.now()}`,
    project_id: projectId,
    title: "Project Research Notes",
    content: "# Research Notes\n\n- Write findings, hypotheses, and paper takeaways here.\n- Markdown formatting supported.",
    updated_at: new Date().toISOString(),
  };

  const [title, setTitle] = useState(existingNote.title);
  const [content, setContent] = useState(existingNote.content);
  const [mode, setMode] = useState<"edit" | "preview">("edit");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    saveNote({
      id: existingNote.id,
      project_id: projectId,
      title,
      content,
      updated_at: new Date().toISOString(),
    });
    setSaved(true);
    addToast({ type: "success", title: "Note Saved", message: "Markdown notes auto-saved cleanly." });
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <Card variant="glass" className="space-y-4">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            Project Rich Notes
          </CardTitle>
          <CardDescription>Collaborative Markdown research notes and hypotheses</CardDescription>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode(mode === "edit" ? "preview" : "edit")}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-300 hover:text-white"
          >
            {mode === "edit" ? "Preview Markdown" : "Edit Markdown"}
          </button>
          <Button variant="primary" size="sm" onClick={handleSave} leftIcon={saved ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Save className="w-4 h-4" />}>
            {saved ? "Saved" : "Save Notes"}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Note Title..."
          className="w-full text-base font-bold bg-transparent border-b border-slate-800 text-slate-100 pb-2 focus:outline-none focus:border-indigo-500"
        />

        {mode === "edit" ? (
          <textarea
            rows={12}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full font-mono text-xs p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        ) : (
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 prose dark:prose-invert text-xs text-slate-300 min-h-[300px] whitespace-pre-wrap">
            {content}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
