import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "../services/dashboard-service";

export function useSystemHealth() {
  return useQuery({
    queryKey: ["system_health"],
    queryFn: () => dashboardService.getSystemHealth(),
    refetchInterval: 30000,
  });
}

export function useActiveWorkflows() {
  return useQuery({
    queryKey: ["active_workflows"],
    queryFn: () => dashboardService.getActiveWorkflows(),
    refetchInterval: 10000,
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: () => dashboardService.getNotifications(),
  });
}

export function useMetricsSeries() {
  return useQuery({
    queryKey: ["metrics_series"],
    queryFn: () => dashboardService.getMetricsSeries(),
  });
}
