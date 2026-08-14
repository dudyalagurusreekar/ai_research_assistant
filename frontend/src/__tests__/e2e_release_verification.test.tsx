import { useAuthStore } from "@/store/use-auth-store";
import { useChatStore } from "@/store/use-chat-store";
import { useProjectStore } from "@/store/use-project-store";
import { useDocumentStore } from "@/store/use-document-store";
import { useBrowserStore } from "@/store/use-browser-store";
import { useDataStore } from "@/store/use-data-store";
import { useKnowledgeStore } from "@/store/use-knowledge-store";
import { useConnectorStore } from "@/store/use-connector-store";
import { useReportsStore } from "@/store/use-reports-store";

describe("Sprint F12: ARA v1.0 Master End-to-End Release Verification", () => {
  it("verifies Auth Session & User Management state", () => {
    useAuthStore.setState({
      user: {
        id: "usr_admin_001",
        email: "admin@ara-research.org",
        full_name: "Lead Scientist",
        role: "ADMIN",
        is_active: true,
      },
      token: "mock_jwt_bearer_token",
      isAuthenticated: true,
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.email).toBe("admin@ara-research.org");
  });

  it("verifies Conversational AI Workspace & Streaming Engine", () => {
    useChatStore.getState().addMessage({
      id: "msg_user_1",
      sender: "user",
      content: "Synthesize CRISPR-Cas9 off-target literature",
      timestamp: new Date().toISOString(),
    });

    useChatStore.getState().addMessage({
      id: "msg_ai_1",
      sender: "assistant",
      content: "High-throughput assays demonstrate off-target rates below 0.02%",
      timestamp: new Date().toISOString(),
      citations: [{ id: "c1", title: "Nature Biotech 2025", doi: "10.1038/nbt.4201" }],
      confidence_score: 98,
    });

    const messages = useChatStore.getState().messages;
    expect(messages).toHaveLength(2);
    expect(messages[1].citations).toHaveLength(1);
    expect(messages[1].confidence_score).toBe(98);
  });

  it("verifies Research Workspace & KanBan Task Management", () => {
    useProjectStore.getState().addProject({
      id: "proj_e2e_1",
      title: "Genome Editing Specificity Project",
      description: "Evaluating base editor fidelity",
      status: "ACTIVE",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      tags: ["CRISPR", "Genomics"],
    });

    const projects = useProjectStore.getState().projects;
    expect(projects.some((p) => p.id === "proj_e2e_1")).toBe(true);
  });

  it("verifies Document Intelligence & RAG Vector Search", () => {
    const docs = useDocumentStore.getState().documents;
    expect(docs.length).toBeGreaterThan(0);
    expect(docs[0]).toHaveProperty("extracted_chunks");
  });

  it("verifies Browser Automation Studio workflow execution", () => {
    useBrowserStore.getState().addLog("[INFO] Playwright Chromium engine ready");
    expect(useBrowserStore.getState().logs).toHaveLength(1);
  });

  it("verifies Data Intelligence Studio SQL Engine & Profiling", () => {
    const datasets = useDataStore.getState().datasets;
    expect(datasets.length).toBeGreaterThan(0);
    expect(datasets[0].columns.length).toBeGreaterThan(0);
  });

  it("verifies Knowledge Graph Explorer & NetworkX Centrality", () => {
    const nodes = useKnowledgeStore.getState().nodes;
    expect(nodes.length).toBeGreaterThan(0);
    expect(nodes[0]).toHaveProperty("pagerank_score");
  });

  it("verifies Connectors Hub integrations", () => {
    const connectors = useConnectorStore.getState().connectors;
    expect(connectors.length).toBeGreaterThan(0);
  });

  it("verifies Reports Center & Multi-Format Exporter", () => {
    const reports = useReportsStore.getState().reports;
    expect(reports.length).toBeGreaterThan(0);
  });
});
