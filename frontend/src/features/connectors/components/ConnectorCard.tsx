"use client";

import React, { useState } from "react";
import { ConnectorProvider, useConnectorStore } from "@/store/use-connector-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { RefreshCw, Sliders, CheckCircle2, AlertCircle, Link2, FileText, Code, Database, MessageSquare } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";
import { connectorService } from "../services/connector-service";

export function ConnectorCard({ connector }: { connector: ConnectorProvider }) {
  const { updateConnectorStatus, setSelectedConnector, setConfigDrawerOpen, addSyncLog } = useConnectorStore();
  const { addToast } = useUIStore();
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    setIsSyncing(true);
    addToast({ type: "info", title: "Syncing Connector", message: `Fetching new data from ${connector.name}...` });

    const log = await connectorService.triggerSync(connector.id);
    addSyncLog(log);

    updateConnectorStatus(connector.id, "CONNECTED", "Just now");
    setIsSyncing(false);
    addToast({ type: "success", title: "Sync Complete", message: `Synced ${log.items_synced} items cleanly.` });
  };

  const handleConfigure = () => {
    setSelectedConnector(connector);
    setConfigDrawerOpen(true);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "LITERATURE":
        return <FileText className="w-5 h-5 text-indigo-400" />;
      case "DEVELOPER":
        return <Code className="w-5 h-5 text-cyan-400" />;
      case "CLOUD_STORAGE":
        return <Database className="w-5 h-5 text-emerald-400" />;
      case "COMMUNICATION":
        return <MessageSquare className="w-5 h-5 text-purple-400" />;
      default:
        return <Link2 className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <Card variant="glass" className="hover:scale-[1.01] transition-all duration-200 flex flex-col justify-between">
      <CardHeader>
        <div className="flex items-center justify-between mb-2">
          <Badge variant={connector.status === "CONNECTED" ? "success" : connector.status === "ERROR" ? "error" : "neutral"}>
            {connector.status}
          </Badge>
          <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">{connector.auth_type}</span>
        </div>

        <CardTitle className="text-base font-bold text-slate-100 flex items-center gap-2.5">
          {getCategoryIcon(connector.category)}
          <span>{connector.name}</span>
        </CardTitle>

        <CardDescription className="line-clamp-2 text-xs">
          {connector.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800">
          <span>Synced: <strong className="text-slate-200">{connector.synced_items_count} items</strong></span>
          <span className="text-[11px]">{connector.last_sync || "Never"}</span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            className="flex-1"
            isLoading={isSyncing}
            onClick={handleSync}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Sync Now
          </Button>

          <button
            onClick={handleConfigure}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            title="Configure Integration"
          >
            <Sliders className="w-4 h-4" />
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
