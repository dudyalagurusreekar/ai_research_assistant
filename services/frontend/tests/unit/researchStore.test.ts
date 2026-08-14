import { describe, it, expect, beforeEach } from "vitest";
import { useResearchStore } from "../../src/stores/researchStore";

describe("useResearchStore", () => {
  beforeEach(() => {
    useResearchStore.getState().resetWorkspace();
  });

  it("should add a message correctly", () => {
    useResearchStore.getState().addMessage({
      sender_type: "USER",
      content: "Explain Cas12a off-target rate",
    });

    const messages = useResearchStore.getState().messages;
    expect(messages.length).toBe(1);
    expect(messages[0].content).toBe("Explain Cas12a off-target rate");
    expect(messages[0].sender_type).toBe("USER");
  });

  it("should set research execution plan", () => {
    const mockPlan = {
      plan_id: "plan_test_99",
      sub_tasks: [
        { task_id: "t1", title: "Literature Search", task_type: "rag_search" },
      ],
      execution_waves: [["t1"]],
      selected_tools: ["rag_search"],
    };

    useResearchStore.getState().setPlan(mockPlan);

    const plan = useResearchStore.getState().currentPlan;
    expect(plan?.plan_id).toBe("plan_test_99");
    expect(plan?.sub_tasks.length).toBe(1);
  });

  it("should set selected model and reasoning mode", () => {
    useResearchStore.getState().setSelectedModel("gemini-2.5-flash");
    useResearchStore.getState().setReasoningMode("deep");

    expect(useResearchStore.getState().selectedModel).toBe("gemini-2.5-flash");
    expect(useResearchStore.getState().reasoningMode).toBe("deep");
  });

  it("should add uploaded document file", () => {
    const mockFile = {
      id: "doc_123",
      filename: "crispr_paper.pdf",
      file_size: 102400,
      mime_type: "application/pdf",
      status: "ready" as const,
      created_at: new Date().toISOString(),
    };

    useResearchStore.getState().addUploadedFile(mockFile);

    const files = useResearchStore.getState().uploadedFiles;
    expect(files.length).toBe(1);
    expect(files[0].filename).toBe("crispr_paper.pdf");
  });
});
