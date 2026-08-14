import { create } from "zustand";

export type ActionType = "NAVIGATE" | "CLICK_ELEMENT" | "TYPE_TEXT" | "EXTRACT_TABLE" | "DOWNLOAD_PDF" | "CAPTURE_SCREENSHOT";

export interface WorkflowStep {
  id: string;
  action: ActionType;
  target?: string;
  value?: string;
  status: "pending" | "running" | "completed" | "failed";
}

export interface ExtractedDataItem {
  id: string;
  title: string;
  url: string;
  extracted_at: string;
  data: Record<string, any>;
}

export interface ScreenshotItem {
  id: string;
  url: string;
  captured_at: string;
  title: string;
}

export interface DownloadItem {
  id: string;
  filename: string;
  file_size: string;
  download_url: string;
  downloaded_at: string;
}

interface BrowserState {
  sessionId: string | null;
  activeUrl: string;
  isExecuting: boolean;
  status: "idle" | "running" | "completed" | "failed";
  workflowSteps: WorkflowStep[];
  logs: string[];
  extractedData: ExtractedDataItem[];
  screenshots: ScreenshotItem[];
  downloads: DownloadItem[];

  // Actions
  setSessionId: (id: string | null) => void;
  setActiveUrl: (url: string) => void;
  setIsExecuting: (executing: boolean) => void;
  setStatus: (status: "idle" | "running" | "completed" | "failed") => void;

  setWorkflowSteps: (steps: WorkflowStep[]) => void;
  addWorkflowStep: (step: WorkflowStep) => void;
  updateWorkflowStepStatus: (id: string, status: WorkflowStep["status"]) => void;

  addLog: (log: string) => void;
  clearLogs: () => void;

  addExtractedData: (item: ExtractedDataItem) => void;
  addScreenshot: (item: ScreenshotItem) => void;
  addDownload: (item: DownloadItem) => void;
}

export const useBrowserStore = create<BrowserState>((set) => ({
  sessionId: "brw_session_001",
  activeUrl: "https://pubmed.ncbi.nlm.nih.gov/?term=CRISPR+Cas9+specificity",
  isExecuting: false,
  status: "idle",
  workflowSteps: [],
  logs: [],
  extractedData: [],
  screenshots: [],
  downloads: [],

  setSessionId: (id) => set({ sessionId: id }),
  setActiveUrl: (url) => set({ activeUrl: url }),
  setIsExecuting: (executing) => set({ isExecuting: executing }),
  setStatus: (status) => set({ status }),

  setWorkflowSteps: (steps) => set({ workflowSteps: steps }),
  addWorkflowStep: (step) => set((state) => ({ workflowSteps: [...state.workflowSteps, step] })),
  updateWorkflowStepStatus: (id, status) =>
    set((state) => ({
      workflowSteps: state.workflowSteps.map((s) => (s.id === id ? { ...s, status } : s)),
    })),

  addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
  clearLogs: () => set({ logs: [] }),

  addExtractedData: (item) => set((state) => ({ extractedData: [item, ...state.extractedData] })),
  addScreenshot: (item) => set((state) => ({ screenshots: [item, ...state.screenshots] })),
  addDownload: (item) => set((state) => ({ downloads: [item, ...state.downloads] })),
}));
