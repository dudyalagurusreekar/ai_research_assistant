"use client";

import React, { useState } from "react";
import { useProjectStore } from "@/store/use-project-store";
import { ProjectCard } from "@/features/projects/components/ProjectCard";
import { CreateProjectModal } from "@/features/projects/components/CreateProjectModal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Microscope, Plus, Search, Folder, Filter } from "lucide-react";

export default function ResearchPage() {
  const { projects } = useProjectStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeDomain, setActiveDomain] = useState<string>("all");
  const [modalOpen, setModalOpen] = useState(false);

  const filtered = projects.filter((p) => {
    const matchesSearch =
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDomain = activeDomain === "all" || p.domain === activeDomain;
    return matchesSearch && matchesDomain;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Microscope className="w-6 h-6 text-indigo-500" />
            Research Workspace & Projects
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Manage multi-agent literature projects, document corpuses, notes, and task boards
          </p>
        </div>

        <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setModalOpen(true)}>
          New Project
        </Button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="w-full sm:w-80">
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {["all", "Biomedical & Genomics", "Structural Biology", "Cheminformatics", "Machine Learning & AI"].map((dom) => (
            <button
              key={dom}
              onClick={() => setActiveDomain(dom)}
              className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
                activeDomain === dom
                  ? "bg-indigo-600 text-white shadow-glow-indigo"
                  : "bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 border border-slate-200 dark:border-slate-800"
              }`}
            >
              {dom === "all" ? "All Domains" : dom}
            </button>
          ))}
        </div>
      </div>

      {/* Project Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((proj) => (
          <ProjectCard key={proj.id} project={proj} />
        ))}
      </div>

      <CreateProjectModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
