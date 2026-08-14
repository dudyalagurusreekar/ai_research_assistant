import { create } from "zustand";

export interface ProjectTask {
  id: string;
  project_id: string;
  title: string;
  status: "todo" | "in_progress" | "done";
  priority: "high" | "medium" | "low";
  due_date?: string;
}

export interface ProjectNote {
  id: string;
  project_id: string;
  title: string;
  content: string;
  updated_at: string;
}

export interface ProjectReport {
  id: string;
  project_id: string;
  title: string;
  summary: string;
  content: string;
  created_at: string;
}

export interface ProjectItem {
  id: string;
  title: string;
  description: string;
  ai_summary: string;
  status: "active" | "archived" | "draft";
  domain: string;
  document_count: number;
  task_count: number;
  updated_at: string;
}

interface ProjectState {
  projects: ProjectItem[];
  selectedProjectId: string | null;
  tasks: ProjectTask[];
  notes: ProjectNote[];
  reports: ProjectReport[];

  // Actions
  setSelectedProjectId: (id: string | null) => void;
  setProjects: (projects: ProjectItem[]) => void;
  addProject: (project: ProjectItem) => void;
  updateProject: (id: string, data: Partial<ProjectItem>) => void;
  deleteProject: (id: string) => void;

  addTask: (task: ProjectTask) => void;
  updateTaskStatus: (taskId: string, status: "todo" | "in_progress" | "done") => void;

  saveNote: (note: ProjectNote) => void;
  addReport: (report: ProjectReport) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [
    {
      id: "prj_001",
      title: "CRISPR-Cas9 Base Editor Off-Target Specificity",
      description: "Literature review and off-target cleavage rate benchmarking across human cell lines.",
      ai_summary: "42 papers indexed into knowledge graph. NetworkX graph centrality identifies high-fidelity Cas9 variants.",
      status: "active",
      domain: "Biomedical & Genomics",
      document_count: 12,
      task_count: 4,
      updated_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: "prj_002",
      title: "AlphaFold 3 Multimer Structure Prediction",
      description: "Structural similarity search and PDB coordinate alignment for protein-ligand complexes.",
      ai_summary: "PDB files processed. TM-score 0.94 achieved for targeted domain binding site.",
      status: "active",
      domain: "Structural Biology",
      document_count: 8,
      task_count: 2,
      updated_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: "prj_003",
      title: "OpenFDA Adverse Drug Reaction Telemetry",
      description: "Pharmacovigilance signals and safety event extraction for oncology therapeutics.",
      ai_summary: "openFDA REST API telemetry ingested into pgvector.",
      status: "active",
      domain: "Cheminformatics",
      document_count: 15,
      task_count: 6,
      updated_at: new Date(Date.now() - 14400000).toISOString(),
    },
  ],
  selectedProjectId: "prj_001",
  tasks: [],
  notes: [],
  reports: [],

  setSelectedProjectId: (id) => set({ selectedProjectId: id }),
  setProjects: (projects) => set({ projects }),
  addProject: (project) => set((state) => ({ projects: [project, ...state.projects] })),
  updateProject: (id, data) =>
    set((state) => ({
      projects: state.projects.map((p) => (p.id === id ? { ...p, ...data } : p)),
    })),
  deleteProject: (id) =>
    set((state) => ({
      projects: state.projects.filter((p) => p.id !== id),
    })),

  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTaskStatus: (taskId, status) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === taskId ? { ...t, status } : t)),
    })),

  saveNote: (note) =>
    set((state) => {
      const idx = state.notes.findIndex((n) => n.id === note.id);
      if (idx >= 0) {
        const updated = [...state.notes];
        updated[idx] = note;
        return { notes: updated };
      }
      return { notes: [...state.notes, note] };
    }),
  addReport: (report) => set((state) => ({ reports: [report, ...state.reports] })),
}));
