import { useReportsStore } from "@/store/use-reports-store";
import { reportsService } from "@/features/reports/services/reports-service";

describe("Sprint F11: Reports, Administration & Settings Center Verification", () => {
  beforeEach(() => {
    useReportsStore.setState({
      reports: [
        {
          id: "rep_001",
          title: "CRISPR-Cas9 Off-Target Cleavage Synthesis Report",
          summary: "Comprehensive synthesis",
          content: "# Synthesis Report",
          status: "completed",
          format: "markdown",
          created_at: new Date().toISOString(),
          author: "Administrator",
        },
      ],
      selectedReport: null,
      templates: [],
      auditLogs: [],
      previewOpen: false,
    });
  });

  it("duplicates reports cleanly", () => {
    const original = useReportsStore.getState().reports[0];
    const dup = {
      ...original,
      id: "rep_dup_1",
      title: `${original.title} (Copy)`,
    };

    useReportsStore.getState().addReport(dup);
    expect(useReportsStore.getState().reports).toHaveLength(2);
    expect(useReportsStore.getState().reports[0].title).toContain("(Copy)");
  });

  it("deletes report item cleanly", () => {
    useReportsStore.getState().deleteReport("rep_001");
    expect(useReportsStore.getState().reports).toHaveLength(0);
  });

  it("fetches audit logs cleanly", async () => {
    const logs = await reportsService.fetchAuditLogs();
    expect(logs).toBeDefined();
    expect(logs.length).toBeGreaterThan(0);
  });
});
