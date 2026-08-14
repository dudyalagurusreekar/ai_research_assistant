"use client";

import React from "react";
import { ProjectItem, useProjectStore } from "@/store/use-project-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Folder, FileText, CheckSquare, Sparkles, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

export function ProjectCard({ project }: { project: ProjectItem }) {
  const router = useRouter();
  const { setSelectedProjectId } = useProjectStore();

  const handleOpen = () => {
    setSelectedProjectId(project.id);
    router.push(`/projects/${project.id}`);
  };

  return (
    <Card variant="glass" className="hover:scale-[1.01] transition-all duration-200 flex flex-col justify-between">
      <CardHeader>
        <div className="flex items-center justify-between mb-2">
          <Badge variant={project.status === "active" ? "brand" : "neutral"}>
            {project.status}
          </Badge>
          <span className="text-[11px] font-semibold text-cyan-400">{project.domain}</span>
        </div>

        <CardTitle className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <Folder className="w-5 h-5 text-indigo-400 shrink-0" />
          <span className="truncate">{project.title}</span>
        </CardTitle>

        <CardDescription className="line-clamp-2 text-xs">
          {project.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* AI Summary Callout */}
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> AI Summary
          </span>
          <p className="text-slate-300 leading-relaxed text-[11px]">{project.ai_summary}</p>
        </div>

        {/* Stats Row */}
        <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800">
          <span className="flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-emerald-400" />
            {project.document_count} Documents
          </span>
          <span className="flex items-center gap-1">
            <CheckSquare className="w-3.5 h-3.5 text-cyan-400" />
            {project.task_count} Tasks
          </span>
          <Button variant="ghost" size="sm" onClick={handleOpen} rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
            Open
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
