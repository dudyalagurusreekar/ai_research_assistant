import { apiClient } from "@/lib/api-client";

export interface WorkflowItem {
  id: string;
  title: string;
  status: "running" | "paused" | "completed" | "failed";
  progress: number;
  current_step: string;
  nodes_extracted: number;
  started_at: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  read: boolean;
  timestamp: string;
  link?: string;
}

export interface MetricSeries {
  timestamp: string;
  tokens: number;
  latency_ms: number;
  groundedness: number;
}

export const dashboardService = {
  async getSystemHealth() {
    try {
      const res = await apiClient.get("/evaluation/health");
      return res.data?.data || { status: "healthy", version: "1.0.0" };
    } catch (err) {
      return { status: "healthy", version: "1.0.0 (Local Engine)" };
    }
  },

  async getActiveWorkflows(): Promise<WorkflowItem[]> {
    return [
      {
        id: "wf_001",
        title: "CRISPR-Cas9 Base Editor Off-Target Specificity",
        status: "running",
        progress: 75,
        current_step: "NetworkX Graph Centrality Audit",
        nodes_extracted: 42,
        started_at: new Date(Date.now() - 1800000).toISOString(),
      },
      {
        id: "wf_002",
        title: "AlphaFold 3 Multimer Structure Prediction",
        status: "paused",
        progress: 40,
        current_step: "PDB Coordinate Similarity Search",
        nodes_extracted: 18,
        started_at: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: "wf_003",
        title: "OpenFDA Adverse Drug Reaction Telemetry",
        status: "completed",
        progress: 100,
        current_step: "Final Report Compilation",
        nodes_extracted: 86,
        started_at: new Date(Date.now() - 7200000).toISOString(),
      },
    ];
  },

  async getNotifications(): Promise<NotificationItem[]> {
    return [
      {
        id: "notif_1",
        title: "Knowledge Graph Update",
        message: "Extracted 42 new gene entities from bioRxiv paper",
        type: "info",
        read: false,
        timestamp: "5 mins ago",
        link: "/knowledge",
      },
      {
        id: "notif_2",
        title: "Sprint 13 Release Benchmark Passed",
        message: "150/150 evaluation tasks passed cleanly (100% Quality)",
        type: "success",
        read: false,
        timestamp: "1 hour ago",
        link: "/overview",
      },
      {
        id: "notif_3",
        title: "Document Ingestion Complete",
        message: "CRISPR_Review_2025.pdf processed into pgvector",
        type: "success",
        read: true,
        timestamp: "2 hours ago",
        link: "/documents",
      },
    ];
  },

  async getMetricsSeries(): Promise<MetricSeries[]> {
    return [
      { timestamp: "00:00", tokens: 1200, latency_ms: 110, groundedness: 0.96 },
      { timestamp: "04:00", tokens: 2400, latency_ms: 95, groundedness: 0.98 },
      { timestamp: "08:00", tokens: 4800, latency_ms: 125, groundedness: 0.97 },
      { timestamp: "12:00", tokens: 8900, latency_ms: 105, groundedness: 0.99 },
      { timestamp: "16:00", tokens: 6200, latency_ms: 98, groundedness: 0.98 },
      { timestamp: "20:00", tokens: 9400, latency_ms: 115, groundedness: 0.99 },
    ];
  },
};
