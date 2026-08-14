import { useConnectorStore } from "@/store/use-connector-store";
import { connectorService } from "@/features/connectors/services/connector-service";

describe("Sprint F10: Connectors Hub & Integration Center Verification", () => {
  beforeEach(() => {
    useConnectorStore.setState({
      connectors: [
        {
          id: "pubmed",
          name: "PubMed E-Utilities",
          category: "LITERATURE",
          description: "Biomedical literature citations",
          status: "CONNECTED",
          last_sync: "10 mins ago",
          synced_items_count: 1420,
          auth_type: "API_KEY",
        },
        {
          id: "github",
          name: "GitHub Enterprise",
          category: "DEVELOPER",
          description: "Repository code search",
          status: "AVAILABLE",
          synced_items_count: 0,
          auth_type: "OAUTH",
        },
      ],
      syncLogs: [],
      activeSyncingId: null,
      configDrawerOpen: false,
      selectedConnector: null,
    });
  });

  it("updates connector status cleanly when triggered", () => {
    useConnectorStore.getState().updateConnectorStatus("github", "CONNECTED", "Just now");

    const github = useConnectorStore.getState().connectors.find((c) => c.id === "github");
    expect(github?.status).toBe("CONNECTED");
    expect(github?.last_sync).toBe("Just now");
  });

  it("triggers manual sync and appends sync log", async () => {
    const log = await connectorService.triggerSync("pubmed");
    useConnectorStore.getState().addSyncLog(log);

    expect(log.status).toBe("success");
    expect(useConnectorStore.getState().syncLogs).toHaveLength(1);
    expect(useConnectorStore.getState().syncLogs[0].provider_id).toBe("pubmed");
  });
});
