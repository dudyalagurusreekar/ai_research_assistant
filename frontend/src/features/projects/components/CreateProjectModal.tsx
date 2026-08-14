"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useProjectStore } from "@/store/use-project-store";
import { useUIStore } from "@/store/use-ui-store";
import { projectService } from "../services/project-service";
import { FolderPlus } from "lucide-react";

export function CreateProjectModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { addProject } = useProjectStore();
  const { addToast } = useUIStore();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [domain, setDomain] = useState("Biomedical & Genomics");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsLoading(true);
    try {
      const newProj = await projectService.createProject({ title, description, domain });
      addProject(newProj);
      addToast({ type: "success", title: "Project Created", message: `Workspace "${title}" is ready.` });
      setTitle("");
      setDescription("");
      onClose();
    } catch (err: any) {
      addToast({ type: "error", title: "Creation Failed", message: "Unable to create project." });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Research Project">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Project Title"
          placeholder="e.g. CRISPR Off-Target Cleavage Assay"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">Project Description & Goal</label>
          <textarea
            rows={3}
            placeholder="Describe research objectives, target literature, or dataset scope..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full text-xs p-3 rounded-xl bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">Research Domain Focus</label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full text-xs font-semibold p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 focus:outline-none"
          >
            <option value="Biomedical & Genomics">Biomedical & Genomics</option>
            <option value="Machine Learning & AI">Machine Learning & AI</option>
            <option value="Cheminformatics">Cheminformatics</option>
            <option value="Structural Biology">Structural Biology</option>
          </select>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
            leftIcon={<FolderPlus className="w-4 h-4" />}
          >
            Initialize Project
          </Button>
        </div>
      </form>
    </Modal>
  );
}
