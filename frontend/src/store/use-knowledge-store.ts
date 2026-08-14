import { create } from "zustand";

export type EntityType = "PROTEIN" | "GENE" | "COMPOUND" | "CELL_LINE" | "PAPER";

export interface GraphNode {
  id: string;
  name: string;
  type: EntityType;
  pagerank_score: number;
  degree: number;
  description: string;
  sensitivity: "PUBLIC" | "RESTRICTED" | "CONFIDENTIAL";
  pii_status: "CLEAN" | "REDACTED";
  evidence_count: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: "TARGETS" | "INHIBITS" | "EXPRESSED_IN" | "SYNTHESIZED_BY" | "CITED_IN";
  confidence: number;
}

export interface MemoryItem {
  id: string;
  category: "USER_PREFERENCE" | "PROJECT_CONTEXT" | "EPISODIC_EXECUTION";
  key: string;
  value: string;
  retention_policy: "PERMANENT" | "30_DAYS" | "SESSION_ONLY";
  created_at: string;
}

interface KnowledgeState {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  filterType: EntityType | "ALL";
  searchQuery: string;
  memories: MemoryItem[];

  // Actions
  setNodes: (nodes: GraphNode[]) => void;
  setEdges: (edges: GraphEdge[]) => void;
  setSelectedNode: (node: GraphNode | null) => void;
  setFilterType: (type: EntityType | "ALL") => void;
  setSearchQuery: (query: string) => void;
  setMemories: (memories: MemoryItem[]) => void;
  addMemory: (memory: MemoryItem) => void;
  deleteMemory: (id: string) => void;
}

export const useKnowledgeStore = create<KnowledgeState>((set) => ({
  nodes: [
    { id: "n1", name: "SpCas9-HF1", type: "PROTEIN", pagerank_score: 0.94, degree: 12, description: "High-fidelity Cas9 endonuclease variant", sensitivity: "PUBLIC", pii_status: "CLEAN", evidence_count: 14 },
    { id: "n2", name: "EMX1 Gene", type: "GENE", pagerank_score: 0.88, degree: 8, description: "Human homeobox gene target locus", sensitivity: "PUBLIC", pii_status: "CLEAN", evidence_count: 9 },
    { id: "n3", name: "VEGFA Gene", type: "GENE", pagerank_score: 0.85, degree: 7, description: "Vascular endothelial growth factor A", sensitivity: "PUBLIC", pii_status: "CLEAN", evidence_count: 11 },
    { id: "n4", name: "OffTargetCleavage", type: "COMPOUND", pagerank_score: 0.79, degree: 5, description: "Non-specific double-strand break assay", sensitivity: "PUBLIC", pii_status: "CLEAN", evidence_count: 6 },
    { id: "n5", name: "HEK293T", type: "CELL_LINE", pagerank_score: 0.82, degree: 9, description: "Human embryonic kidney cell line", sensitivity: "PUBLIC", pii_status: "CLEAN", evidence_count: 18 },
  ],
  edges: [
    { id: "e1", source: "n1", target: "n2", relation: "TARGETS", confidence: 0.98 },
    { id: "e2", source: "n1", target: "n3", relation: "TARGETS", confidence: 0.94 },
    { id: "e3", source: "n1", target: "n4", relation: "INHIBITS", confidence: 0.91 },
    { id: "e4", source: "n1", target: "n5", relation: "EXPRESSED_IN", confidence: 0.96 },
  ],
  selectedNode: null,
  filterType: "ALL",
  searchQuery: "",
  memories: [
    { id: "mem_1", category: "USER_PREFERENCE", key: "default_embedding_model", value: "gemini-embedding-2 (1536-dim)", retention_policy: "PERMANENT", created_at: "2026-08-04T10:00:00Z" },
    { id: "mem_2", category: "PROJECT_CONTEXT", key: "crispr_off_target_threshold", value: "Z-score > 2.5", retention_policy: "30_DAYS", created_at: "2026-08-04T10:30:00Z" },
  ],

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  setFilterType: (type) => set({ filterType: type }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setMemories: (memories) => set({ memories }),
  addMemory: (memory) => set((state) => ({ memories: [memory, ...state.memories] })),
  deleteMemory: (id) => set((state) => ({ memories: state.memories.filter((m) => m.id !== id) })),
}));
