"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useProjectStore } from "@/store/use-project-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ProjectTaskManager } from "@/features/projects/components/ProjectTaskManager";
import { ProjectNotesEditor } from "@/features/projects/components/ProjectNotesEditor";
import { ProjectReportsView } from "@/features/projects/components/ProjectReportsView";
import {
  Folder,
  CheckSquare,
  FileText,
  Sparkles,
  ArrowLeft,
  Clock,
  MessageSquare,
  Bot,
} from "lucide-react";
import Link from "next/link";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = (params?.id as string) || "prj_001";
  const { projects } = useProjectStore();

  const project = projects.find((p) => p.id === projectId) || projects[0];
  const [activeTab, setActiveTab] = useState<"overview" | "tasks" | "notes" | "reports">("overview");

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl glass-card border border-indigo-500/20 shadow-glow-indigo">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push("/research")}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Folder className="w-6 h-6 text-indigo-400" />
              {project.title}
            </h1>
            <Badge variant="brand">{project.domain}</Badge>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">{project.description}</p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link href={`/chat?project_id=${project.id}`}>
            <Button variant="primary" leftIcon={<MessageSquare className="w-4 h-4" />}>
              Launch Project AI Chat
            </Button>
          </Link>
        </div>
      </div>

      {/* Workspace Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("overview")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "overview" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Overview & Summary
        </button>

        <button
          onClick={() => setActiveTab("tasks")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "tasks" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <CheckSquare className="w-4 h-4" />
          Task Board
        </button>

        <button
          onClick={() => setActiveTab("notes")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "notes" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <FileText className="w-4 h-4" />
          Markdown Notes
        </button>

        <button
          onClick={() => setActiveTab("reports")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "reports" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Bot className="w-4 h-4" />
          Synthesis Reports
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card variant="glass" className="lg:col-span-2">
            <CardHeader>
              <CardTitle>AI Summary & Synthesis Overview</CardTitle>
              <CardDescription>Knowledge extractions and RAG corpus metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-indigo-400 block uppercase tracking-wider">
                  Automated Summary
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">{project.ai_summary}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-xs font-semibold text-slate-400">Indexed Documents</span>
                  <h3 className="text-2xl font-bold text-emerald-400 mt-1">{project.document_count}</h3>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-xs font-semibold text-slate-400">Project Tasks</span>
                  <h3 className="text-2xl font-bold text-cyan-400 mt-1">{project.task_count}</h3>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Activity Timeline */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle>Activity Timeline</CardTitle>
              <CardDescription>Recent project execution events</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-200">
                  <span>GUIDE-seq Cleavage Assay</span>
                  <span className="text-[10px] text-slate-400">2 hours ago</span>
                </div>
                <p className="text-[11px] text-slate-400">Task completed cleanly.</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-200">
                  <span>Document Ingested</span>
                  <span className="text-[10px] text-slate-400">1 day ago</span>
                </div>
                <p className="text-[11px] text-slate-400">Added 42 vector chunks to pgvector.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === "tasks" && <ProjectTaskManager projectId={project.id} />}
      {activeTab === "notes" && <ProjectNotesEditor projectId={project.id} />}
      {activeTab === "reports" && <ProjectReportsView projectId={project.id} />}
    </div>
  );
}
