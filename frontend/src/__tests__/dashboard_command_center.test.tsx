import { dashboardService } from "@/features/dashboard/services/dashboard-service";

describe("Sprint F4: AI Dashboard & Research Command Center Verification", () => {
  it("fetches active workflows and verifies progress attributes", async () => {
    const workflows = await dashboardService.getActiveWorkflows();
    expect(workflows.length).toBeGreaterThan(0);
    expect(workflows[0]).toHaveProperty("title");
    expect(workflows[0]).toHaveProperty("progress");
    expect(workflows[0]).toHaveProperty("current_step");
  });

  it("fetches metric series and validates data points", async () => {
    const metrics = await dashboardService.getMetricsSeries();
    expect(metrics).toHaveLength(6);
    expect(metrics[0].groundedness).toBeGreaterThanOrEqual(0.9);
  });

  it("fetches notifications and verifies status types", async () => {
    const notifications = await dashboardService.getNotifications();
    expect(notifications.length).toBeGreaterThan(0);
    expect(notifications[0]).toHaveProperty("type");
    expect(notifications[0]).toHaveProperty("read");
  });
});
