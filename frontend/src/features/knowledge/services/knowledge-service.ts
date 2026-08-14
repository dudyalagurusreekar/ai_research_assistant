import { apiClient } from "@/lib/api-client";
import { GraphNode, GraphEdge, MemoryItem } from "@/store/use-knowledge-store";

export const knowledgeService = {
  async fetchGraphTopology(): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
    try {
      const res = await apiClient.get("/knowledge/graph");
      const data = res.data || (res as any).data;
      if (data?.nodes) {
        return {
          nodes: data.nodes,
          edges: data.edges || [],
        };
      }
      return { nodes: [], edges: [] };
    } catch (err) {
      console.warn("fetchGraphTopology API notice:", err);
      return { nodes: [], edges: [] };
    }
  },

  async fetchLongTermMemory(): Promise<MemoryItem[]> {
    try {
      const res = await apiClient.get("/knowledge/memory");
      const data = res.data || (res as any).data;
      if (data?.memories) return data.memories;
      return [];
    } catch (err) {
      console.warn("fetchLongTermMemory API notice:", err);
      return [];
    }
  },
};
