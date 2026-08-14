"use client";

import React, { useState } from "react";
import { useBrowserStore } from "@/store/use-browser-store";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Globe, RefreshCw, Camera, ArrowLeft, ArrowRight, ShieldCheck, Play } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function LiveBrowserViewer() {
  const { activeUrl, setActiveUrl, isExecuting, status } = useBrowserStore();
  const { addToast } = useUIStore();
  const [urlInput, setUrlInput] = useState(activeUrl);

  const handleNavigate = () => {
    setActiveUrl(urlInput);
    addToast({ type: "info", title: "Navigating Viewport", message: `Playwright loading ${urlInput}` });
  };

  const handleScreenshot = () => {
    addToast({ type: "success", title: "Screenshot Captured", message: "Saved to Screenshots gallery." });
  };

  return (
    <div className="glass-card rounded-2xl border border-slate-200/80 dark:border-slate-800/80 overflow-hidden space-y-0">
      {/* Location Bar Header */}
      <div className="flex items-center justify-between gap-3 px-4 py-3 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <button className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <button className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <ArrowRight className="w-4 h-4" />
          </button>
          <button onClick={handleNavigate} className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* URL Input */}
        <div className="flex-1 relative">
          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-indigo-400" />
          <input
            type="text"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleNavigate()}
            className="w-full pl-9 pr-4 py-1.5 rounded-xl bg-slate-950 text-xs font-mono text-slate-100 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <Badge variant={status === "running" ? "brand" : "success"} size="sm">
            {status === "running" ? "PLAYWRIGHT ACTIVE" : "ENGINE READY"}
          </Badge>

          <Button
            variant="outline"
            size="sm"
            onClick={handleScreenshot}
            leftIcon={<Camera className="w-3.5 h-3.5" />}
          >
            Screenshot
          </Button>
        </div>
      </div>

      {/* Viewport Frame */}
      <div className="h-[420px] bg-slate-950 relative flex flex-col items-center justify-center p-6 text-center overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(#312e81_1px,transparent_1px)] [background-size:20px_20px] opacity-20" />

        <div className="relative z-10 max-w-lg space-y-3">
          <div className="p-4 rounded-full bg-indigo-500/10 text-indigo-400 mx-auto w-16 h-16 flex items-center justify-center border border-indigo-500/20">
            <Globe className="w-8 h-8 animate-pulse" />
          </div>
          <h3 className="text-base font-bold text-slate-100">Playwright Headless Browser Session</h3>
          <p className="text-xs text-slate-400 font-mono">
            Target: <span className="text-indigo-300">{activeUrl}</span>
          </p>
          <div className="flex justify-center gap-2 pt-2">
            <Badge variant="info">Chromium 124.0</Badge>
            <Badge variant="success">Anti-Bot Evasion ON</Badge>
            <Badge variant="brand">Proxy Enabled</Badge>
          </div>
        </div>
      </div>
    </div>
  );
}
