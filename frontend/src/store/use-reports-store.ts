import { create } from "zustand";

export interface GeneratedReport {
  id: string;
  title: string;
  summary: string;
  content: string;
  status: "completed" | "draft" | "scheduled";
  format: "markdown" | "html" | "pdf";
  created_at: string;
  project_id?: string;
  author: string;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  structure_outline: string[];
}

export interface AuditLogEntry {
  id: string;
  event_type: "LOGIN" | "AI_REQUEST" | "REPORT_GEN" | "SETTINGS_CHANGE" | "CONNECTOR_SYNC";
  user: string;
  details: string;
  timestamp: string;
  status: "success" | "warning" | "error";
}

interface ReportsState {
  reports: GeneratedReport[];
  selectedReport: GeneratedReport | null;
  templates: ReportTemplate[];
  auditLogs: AuditLogEntry[];
  previewOpen: boolean;

  // Actions
  setReports: (reports: GeneratedReport[]) => void;
  addReport: (report: GeneratedReport) => void;
  updateReport: (id: string, data: Partial<GeneratedReport>) => void;
  deleteReport: (id: string) => void;
  setSelectedReport: (report: GeneratedReport | null) => void;
  setPreviewOpen: (open: boolean) => void;
  setAuditLogs: (logs: AuditLogEntry[]) => void;
}

export const useReportsStore = create<ReportsState>((set) => ({
  reports: [
    {
      id: "rep_001",
      title: "CRISPR-Cas9 Off-Target Cleavage Synthesis Report",
      summary: "Comprehensive literature synthesis across 42 PubMed & bioRxiv papers.",
      content: "# CRISPR-Cas9 Off-Target Cleavage Synthesis Report\n\n## Executive Summary\nAnalysis of high-fidelity Cas9 variants demonstrates >92% reduction in non-specific genomic cleavage.\n\n## Key Findings\n- SpCas9-HF1 shows undetectable off-target activity at EMX1 site.\n- Vector embeddings in pgvector confirm 0.96 similarity score.",
      status: "completed",
      format: "markdown",
      created_at: new Date(Date.now() - 3600000).toISOString(),
      author: "Administrator",
    },
  ],
  selectedReport: null,
  templates: [
    {
      id: "tpl_1",
      name: "Biomedical Literature Synthesis",
      description: "Standard executive summary, methodology, PubMed citations, and conclusion.",
      structure_outline: ["Abstract", "Literature Review", "Key Findings", "Provenances"],
    },
    {
      id: "tpl_2",
      name: "Cheminformatics Target Profiling",
      description: "Bioactivity tables, IC50 values, ChEMBL mechanism, and safety telemetry.",
      structure_outline: ["Target Overview", "Bioactivity Summary", "Safety Telemetry"],
    },
  ],
  auditLogs: [
    { id: "audit_001", event_type: "LOGIN", user: "admin@ara-research.org", details: "Authenticated via Bearer JWT token", timestamp: new Date(Date.now() - 1800000).toISOString(), status: "success" },
    { id: "audit_002", event_type: "AI_REQUEST", user: "admin@ara-research.org", details: "Intelligent LLM Orchestrator route to Gemini 2.5 Pro", timestamp: new Date(Date.now() - 3600000).toISOString(), status: "success" },
    { id: "audit_003", event_type: "REPORT_GEN", user: "admin@ara-research.org", details: "Synthesized markdown report with 14 citations", timestamp: new Date(Date.now() - 7200000).toISOString(), status: "success" },
  ],
  previewOpen: false,

  setReports: (reports) => set({ reports }),
  addReport: (report) => set((state) => ({ reports: [report, ...state.reports] })),
  updateReport: (id, data) =>
    set((state) => ({
      reports: state.reports.map((r) => (r.id === id ? { ...r, ...data } : r)),
    })),
  deleteReport: (id) => set((state) => ({ reports: state.reports.filter((r) => r.id !== id) })),
  setSelectedReport: (report) => set({ selectedReport: report }),
  setPreviewOpen: (open) => set({ previewOpen: open }),
  setAuditLogs: (logs) => set({ auditLogs: logs }),
}));
