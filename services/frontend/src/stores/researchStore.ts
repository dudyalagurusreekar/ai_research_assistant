import { create } from "zustand";

export interface Citation {
  id: string;
  source_title: string;
  snippet: string;
  url?: string;
  page_number?: number;
  similarity_score?: number;
  author?: string;
}

export interface ChatMessageItem {
  id: string;
  sender_type: "USER" | "ASSISTANT" | "SYSTEM" | "TOOL";
  content: string;
  citations?: Citation[];
  tool_calls?: any[];
  timestamp: string;
  isStreaming?: boolean;
}

export interface SubTaskItem {
  task_id: string;
  title: string;
  description?: string;
  task_type: string;
  status?: "pending" | "running" | "completed" | "failed";
  estimated_complexity?: number;
  output?: string;
}

export interface ExecutionPlan {
  plan_id: string;
  session_id?: string;
  intent?: string;
  complexity_score?: number;
  stage?: string;
  sub_tasks: SubTaskItem[];
  execution_waves: string[][];
  selected_tools: string[];
}

export interface UploadedDocument {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  chunks_count?: number;
  status: "uploaded" | "indexing" | "ready" | "failed";
  created_at: string;
}

interface ResearchState {
  activeSessionId: string | null;
  activeConversationId: string | null;
  messages: ChatMessageItem[];
  currentPlan: ExecutionPlan | null;
  isStreaming: boolean;
  isPlanning: boolean;
  selectedModel: string;
  reasoningMode: "standard" | "deep" | "fast";
  activeCitation: Citation | null;
  uploadedFiles: UploadedDocument[];
  activeReport: any | null;

  // Actions
  setSession: (sessionId: string, conversationId?: string) => void;
  setPlan: (plan: ExecutionPlan | null) => void;
  addMessage: (message: Omit<ChatMessageItem, "id" | "timestamp">) => void;
  updateLastAssistantMessage: (text: string, isStreaming?: boolean) => void;
  setStreaming: (isStreaming: boolean) => void;
  setPlanning: (isPlanning: boolean) => void;
  setSelectedModel: (model: string) => void;
  setReasoningMode: (mode: "standard" | "deep" | "fast") => void;
  setActiveCitation: (citation: Citation | null) => void;
  addUploadedFile: (file: UploadedDocument) => void;
  setActiveReport: (report: any | null) => void;
  resetWorkspace: () => void;
}

export const useResearchStore = create<ResearchState>((set) => ({
  activeSessionId: null,
  activeConversationId: null,
  messages: [
    {
      id: "msg_welcome",
      sender_type: "ASSISTANT",
      content:
        "Welcome to the **ARA Enterprise Research Workspace**. Submit a complex query or research prompt to decompose it into execution DAG waves, retrieve grounded evidence across documents, or execute GraphRAG semantic reasoning.",
      timestamp: new Date().toISOString(),
      citations: [],
    },
  ],
  currentPlan: null,
  isStreaming: false,
  isPlanning: false,
  selectedModel: "gemini-2.5-pro",
  reasoningMode: "standard",
  activeCitation: null,
  uploadedFiles: [],
  activeReport: null,

  setSession: (sessionId, conversationId) =>
    set({
      activeSessionId: sessionId,
      activeConversationId: conversationId || `conv_${sessionId}`,
    }),

  setPlan: (plan) => set({ currentPlan: plan }),

  addMessage: (msg) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...msg,
          id: `msg_${Math.random().toString(36).substring(2, 9)}`,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  updateLastAssistantMessage: (text, isStreaming = false) =>
    set((state) => {
      const newMessages = [...state.messages];
      const lastIdx = newMessages.length - 1;
      if (lastIdx >= 0 && newMessages[lastIdx].sender_type === "ASSISTANT") {
        newMessages[lastIdx] = {
          ...newMessages[lastIdx],
          content: text,
          isStreaming,
        };
      }
      return { messages: newMessages };
    }),

  setStreaming: (isStreaming) => set({ isStreaming }),
  setPlanning: (isPlanning) => set({ isPlanning }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setReasoningMode: (mode) => set({ reasoningMode: mode }),
  setActiveCitation: (citation) => set({ activeCitation: citation }),

  addUploadedFile: (file) =>
    set((state) => ({
      uploadedFiles: [...state.uploadedFiles, file],
    })),

  setActiveReport: (report) => set({ activeReport: report }),

  resetWorkspace: () =>
    set({
      activeSessionId: null,
      activeConversationId: null,
      messages: [],
      currentPlan: null,
      isStreaming: false,
      isPlanning: false,
      activeCitation: null,
      activeReport: null,
    }),
}));
