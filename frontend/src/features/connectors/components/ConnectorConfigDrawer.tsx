"use client";

import React, { useState } from "react";
import { useConnectorStore } from "@/store/use-connector-store";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { X, Sliders, Key, RefreshCw, CheckCircle2 } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function ConnectorConfigDrawer() {
  const { configDrawerOpen, setConfigDrawerOpen, selectedConnector, updateConnectorStatus } = useConnectorStore();
  const { addToast } = useUIStore();

  const [apiKey, setApiKey] = useState("");
  const [syncInterval, setSyncInterval] = useState("1_HOUR");

  if (!configDrawerOpen || !selectedConnector) return null;

  const handleSave = () => {
    updateConnectorStatus(selectedConnector.id, "CONNECTED", "Just now");
    addToast({ type: "success", title: "Configuration Saved", message: `Updated credentials for ${selectedConnector.name}.` });
    setConfigDrawerOpen(false);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-80 sm:w-96 glass-panel shadow-2xl border-l border-slate-200/80 dark:border-slate-800/80 p-5 animate-slide-up flex flex-col justify-between">
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-slate-100">{selectedConnector.name}</h3>
          </div>
          <button onClick={() => setConfigDrawerOpen(false)} className="text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4 text-xs">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-semibold">Integration Provider Status</span>
            <div className="flex items-center justify-between">
              <Badge variant={selectedConnector.status === "CONNECTED" ? "success" : "neutral"}>
                {selectedConnector.status}
              </Badge>
              <span className="text-slate-400 text-[11px]">Auth: {selectedConnector.auth_type}</span>
            </div>
          </div>

          {selectedConnector.auth_type === "API_KEY" ? (
            <Input
              label="API Key / Secret Token"
              type="password"
              placeholder="e.g. pubmed_api_key_xxxxxxxx"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              leftIcon={<Key className="w-4 h-4" />}
            />
          ) : (
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-2">
              <p className="text-slate-300 font-semibold">OAuth 2.0 Authorization Required</p>
              <Button variant="primary" size="sm" className="w-full">
                Authenticate via {selectedConnector.name}
              </Button>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="font-bold text-slate-300">Automatic Sync Interval</label>
            <select
              value={syncInterval}
              onChange={(e) => setSyncInterval(e.target.value)}
              className="w-full text-xs font-semibold p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100"
            >
              <option value="REALTIME">Real-time Webhook</option>
              <option value="15_MINS">Every 15 Minutes</option>
              <option value="1_HOUR">Every 1 Hour (Default)</option>
              <option value="DAILY">Daily Batch</option>
            </select>
          </div>
        </div>
      </div>

      <div className="pt-3 border-t border-slate-800 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={() => setConfigDrawerOpen(false)}>
          Cancel
        </Button>
        <Button variant="primary" className="flex-1" onClick={handleSave} leftIcon={<CheckCircle2 className="w-4 h-4" />}>
          Save Configuration
        </Button>
      </div>
    </div>
  );
}
