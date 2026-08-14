import { apiClient } from "@/lib/api-client";
import { GeneratedReport, AuditLogEntry } from "@/store/use-reports-store";

export const reportsService = {
  async fetchReports(): Promise<GeneratedReport[]> {
    try {
      const res = await apiClient.get("/reports");
      if (res.data?.reports || res.data?.data) return res.data.reports || res.data.data;
      return [];
    } catch (err) {
      console.warn("fetchReports API notice:", err);
      return [];
    }
  },

  async fetchAuditLogs(): Promise<AuditLogEntry[]> {
    try {
      const res = await apiClient.get("/admin/audit");
      if (res.data?.logs || res.data?.data) return res.data.logs || res.data.data;
      return [];
    } catch (err) {
      console.warn("fetchAuditLogs API notice:", err);
      return [];
    }
  },
};
