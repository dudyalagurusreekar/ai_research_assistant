import { useBrowserStore } from "@/store/use-browser-store";
import { browserService } from "@/features/browser/services/browser-service";

describe("Sprint F7: Browser Automation Studio Verification", () => {
  beforeEach(() => {
    useBrowserStore.setState({
      sessionId: "brw_test_001",
      activeUrl: "https://pubmed.ncbi.nlm.nih.gov",
      isExecuting: false,
      status: "idle",
      workflowSteps: [],
      logs: [],
      extractedData: [],
      screenshots: [],
      downloads: [],
    });
  });

  it("configures workflow steps and updates state", () => {
    const step = {
      id: "step_test_1",
      action: "NAVIGATE" as const,
      target: "https://pubmed.ncbi.nlm.nih.gov",
      status: "pending" as const,
    };

    useBrowserStore.getState().addWorkflowStep(step);
    expect(useBrowserStore.getState().workflowSteps).toHaveLength(1);
    expect(useBrowserStore.getState().workflowSteps[0].action).toBe("NAVIGATE");
  });

  it("appends Playwright execution logs cleanly", () => {
    useBrowserStore.getState().addLog("[INFO] Starting Playwright browser engine...");
    expect(useBrowserStore.getState().logs).toHaveLength(1);
    expect(useBrowserStore.getState().logs[0]).toContain("Playwright");
  });

  it("executes workflow and extracts JSON dataset", async () => {
    const steps = [
      { id: "s1", action: "NAVIGATE" as const, target: "https://pubmed.ncbi.nlm.nih.gov", status: "completed" as const },
    ];
    const data = await browserService.executeWorkflow("brw_test_001", steps);
    expect(data).toHaveProperty("data");
    expect(data).toHaveProperty("url");
  });
});
