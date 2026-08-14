import { create } from "zustand";

export type SenderType = "USER" | "ASSISTANT" | "TOOL";

export interface Citation {
  id: string;
  source_title: string;
  url?: string;
  doi?: string;
  snippet?: string;
}

export interface ReasoningStep {
  id: string;
  title: string;
  status: "completed" | "in_progress" | "failed";
  details?: string;
}

export interface ChatMessage {
  id: string;
  sender_type: SenderType;
  content: string;
  timestamp: string;
  citations?: Citation[];
  confidence_score?: number;
  reasoning_steps?: ReasoningStep[];
  tool_calls?: any[];
  isStreaming?: boolean;
}

export interface ConversationThread {
  id: string;
  title: string;
  session_id: string;
  updated_at: string;
  message_count: number;
}

interface ChatState {
  activeSessionId: string | null;
  activeConversationId: string | null;
  conversations: ConversationThread[];
  messages: ChatMessage[];
  isStreaming: boolean;

  // AI Parameters
  selectedModel: string;
  temperature: number;
  enforceRAG: boolean;
  maxTokens: number;

  // Drawers & Uploads
  attachedFiles: File[];
  showExecutionTimeline: boolean;
  showControlDrawer: boolean;

  // Actions
  setActiveSession: (sessionId: string | null) => void;
  setActiveConversation: (convId: string | null) => void;
  setConversations: (convs: ConversationThread[]) => void;
  addConversation: (conv: ConversationThread) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  addMessage: (msg: ChatMessage) => void;
  updateLastAssistantMessage: (chunk: string) => void;
  setIsStreaming: (streaming: boolean) => void;

  setSelectedModel: (model: string) => void;
  setTemperature: (temp: number) => void;
  setEnforceRAG: (enforce: boolean) => void;

  attachFiles: (files: File[]) => void;
  removeAttachedFile: (index: number) => void;
  clearAttachedFiles: () => void;

  toggleExecutionTimeline: () => void;
  toggleControlDrawer: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  activeSessionId: "res_session_default",
  activeConversationId: "conv_main_001",
  conversations: [],
  messages: [],
  isStreaming: false,

  selectedModel: "gemini-2.5-pro",
  temperature: 0.2,
  enforceRAG: true,
  maxTokens: 4096,

  attachedFiles: [],
  showExecutionTimeline: false,
  showControlDrawer: false,

  setActiveSession: (sessionId) => set({ activeSessionId: sessionId }),
  setActiveConversation: (convId) => set({ activeConversationId: convId }),
  setConversations: (convs) => set({ conversations: convs }),
  addConversation: (conv) => set((state) => ({ conversations: [conv, ...state.conversations] })),
  setMessages: (msgs) => set({ messages: msgs }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  updateLastAssistantMessage: (chunk) =>
    set((state) => {
      const msgs = [...state.messages];
      const lastIndex = msgs.length - 1;
      if (lastIndex >= 0 && msgs[lastIndex].sender_type === "ASSISTANT") {
        msgs[lastIndex] = {
          ...msgs[lastIndex],
          content: msgs[lastIndex].content + chunk,
        };
      }
      return { messages: msgs };
    }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),

  setSelectedModel: (model) => set({ selectedModel: model }),
  setTemperature: (temp) => set({ temperature: temp }),
  setEnforceRAG: (enforce) => set({ enforceRAG: enforce }),

  attachFiles: (files) => set((state) => ({ attachedFiles: [...state.attachedFiles, ...files] })),
  removeAttachedFile: (index) =>
    set((state) => ({ attachedFiles: state.attachedFiles.filter((_, i) => i !== index) })),
  clearAttachedFiles: () => set({ attachedFiles: [] }),

  toggleExecutionTimeline: () => set((state) => ({ showExecutionTimeline: !state.showExecutionTimeline })),
  toggleControlDrawer: () => set((state) => ({ showControlDrawer: !state.showControlDrawer })),
}));
