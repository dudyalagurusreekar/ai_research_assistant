import { useChatStore } from "@/store/use-chat-store";

describe("Sprint F3: AI Workspace & Chat Platform Verification", () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      attachedFiles: [],
      isStreaming: false,
      selectedModel: "gemini-2.5-pro",
      temperature: 0.2,
      enforceRAG: true,
    });
  });

  it("adds user and assistant messages to state correctly", () => {
    const userMsg = {
      id: "msg_user_1",
      sender_type: "USER" as const,
      content: "Explain Cas9 endonuclease mechanism.",
      timestamp: new Date().toISOString(),
    };

    useChatStore.getState().addMessage(userMsg);
    expect(useChatStore.getState().messages).toHaveLength(1);
    expect(useChatStore.getState().messages[0].content).toBe("Explain Cas9 endonuclease mechanism.");
  });

  it("updates streaming assistant message chunk by chunk", () => {
    const assistantMsg = {
      id: "msg_ast_1",
      sender_type: "ASSISTANT" as const,
      content: "Cas9 is a ",
      timestamp: new Date().toISOString(),
    };

    useChatStore.getState().addMessage(assistantMsg);
    useChatStore.getState().updateLastAssistantMessage("dual-RNA-guided endonuclease.");

    const messages = useChatStore.getState().messages;
    expect(messages[0].content).toBe("Cas9 is a dual-RNA-guided endonuclease.");
  });

  it("attaches and removes research files", () => {
    const mockFile = new File(["sample paper text"], "paper.pdf", { type: "application/pdf" });
    useChatStore.getState().attachFiles([mockFile]);

    expect(useChatStore.getState().attachedFiles).toHaveLength(1);
    expect(useChatStore.getState().attachedFiles[0].name).toBe("paper.pdf");

    useChatStore.getState().removeAttachedFile(0);
    expect(useChatStore.getState().attachedFiles).toHaveLength(0);
  });

  it("updates model provider and temperature parameters", () => {
    useChatStore.getState().setSelectedModel("ollama-local");
    useChatStore.getState().setTemperature(0.5);

    const state = useChatStore.getState();
    expect(state.selectedModel).toBe("ollama-local");
    expect(state.temperature).toBe(0.5);
  });
});
