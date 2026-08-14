import { create } from "zustand";

export interface ConnectorProvider {
  id: string;
  name: string;
  category: "LITERATURE" | "CLOUD_STORAGE" | "COMMUNICATION" | "DEVELOPER" | "AI_PROVIDER";
  description: string;
  status: "CONNECTED" | "AVAILABLE" | "ERROR";
  last_sync?: string;
  synced_items_count: number;
  auth_type: "OAUTH" | "API_KEY";
}

export interface SyncLog {
  id: string;
  provider_id: string;
  status: "success" | "failed";
  items_synced: number;
  duration_ms: number;
  timestamp: string;
}

interface ConnectorState {
  connectors: ConnectorProvider[];
  syncLogs: SyncLog[];
  activeSyncingId: string | null;
  configDrawerOpen: boolean;
  selectedConnector: ConnectorProvider | null;

  // Actions
  setConnectors: (connectors: ConnectorProvider[]) => void;
  updateConnectorStatus: (id: string, status: ConnectorProvider["status"], lastSync?: string) => void;
  setActiveSyncingId: (id: string | null) => void;
  setConfigDrawerOpen: (open: boolean) => void;
  setSelectedConnector: (connector: ConnectorProvider | null) => void;
  addSyncLog: (log: SyncLog) => void;
}

export const useConnectorStore = create<ConnectorState>((set) => ({
  connectors: [
    { id: "conn_pubmed", name: "PubMed / NCBI E-Utilities", category: "LITERATURE", description: "Search 35M+ biomedical citations & PubMed Central open access XML", status: "CONNECTED", last_sync: "10 mins ago", synced_items_count: 1420, auth_type: "API_KEY" },
    { id: "conn_chembl", name: "ChEMBL Bioactivity DB", category: "AI_PROVIDER", description: "Query 2.4M+ bioactive molecules, IC50 values, and drug target mechanisms", status: "CONNECTED", last_sync: "1 hour ago", synced_items_count: 890, auth_type: "API_KEY" },
    { id: "conn_biorxiv", name: "bioRxiv / medRxiv Preprints", category: "LITERATURE", description: "Real-time life science preprint RSS feed ingestion & full-text extraction", status: "CONNECTED", last_sync: "25 mins ago", synced_items_count: 412, auth_type: "OAUTH" },
    { id: "conn_openfda", name: "openFDA Safety Telemetry", category: "DEVELOPER", description: "FDA adverse event reporting, NDC drug labels, and 510(k) medical device clearance", status: "CONNECTED", last_sync: "3 hours ago", synced_items_count: 650, auth_type: "API_KEY" },
  ],
  syncLogs: [
    { id: "log_1", provider_id: "conn_pubmed", status: "success", items_synced: 142, duration_ms: 310, timestamp: new Date(Date.now() - 600000).toISOString() },
    { id: "log_2", provider_id: "conn_biorxiv", status: "success", items_synced: 28, duration_ms: 195, timestamp: new Date(Date.now() - 1500000).toISOString() },
  ],
  activeSyncingId: null,
  configDrawerOpen: false,
  selectedConnector: null,

  setConnectors: (connectors) => set({ connectors }),
  updateConnectorStatus: (id, status, lastSync) =>
    set((state) => ({
      connectors: state.connectors.map((c) =>
        c.id === id ? { ...c, status, last_sync: lastSync || c.last_sync } : c
      ),
    })),
  setActiveSyncingId: (id) => set({ activeSyncingId: id }),
  setConfigDrawerOpen: (open) => set({ configDrawerOpen: open }),
  setSelectedConnector: (connector) => set({ selectedConnector: connector }),
  addSyncLog: (log) => set((state) => ({ syncLogs: [log, ...state.syncLogs] })),
}));
