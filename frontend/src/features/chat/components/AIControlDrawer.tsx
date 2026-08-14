"use client";

import React from "react";
import { useChatStore } from "@/store/use-chat-store";
import { X, Sliders, Cpu, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function AIControlDrawer() {
  const {
    showControlDrawer,
    toggleControlDrawer,
    selectedModel,
    setSelectedModel,
    temperature,
    setTemperature,
    enforceRAG,
    setEnforceRAG,
  } = useChatStore();

  if (!showControlDrawer) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-80 glass-panel shadow-2xl border-l border-slate-200/80 dark:border-slate-800/80 p-5 animate-slide-up flex flex-col space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-100">AI Model & RAG Controls</h3>
        </div>
        <button onClick={toggleControlDrawer} className="text-slate-400 hover:text-slate-200">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto">
        {/* Model Provider Selection */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
            LLM Provider Engine
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full text-xs font-semibold bg-slate-900 text-slate-200 rounded-xl p-2.5 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="gemini-2.5-pro">Gemini 2.5 Pro (Default)</option>
            <option value="ollama-local">Ollama Local (Offline)</option>
            <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
            <option value="gpt-4o">OpenAI GPT-4o</option>
          </select>
        </div>

        {/* Temperature Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <label className="font-bold uppercase tracking-wider text-slate-400">Temperature</label>
            <span className="font-mono text-indigo-400 font-bold">{temperature}</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full accent-indigo-500 bg-slate-800 rounded-lg cursor-pointer"
          />
          <span className="text-[10px] text-slate-500 block">Lower temperature ensures deterministic research output.</span>
        </div>

        {/* RAG Enforcement Toggle */}
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
          <div className="space-y-0.5">
            <span className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Strict RAG Mode
            </span>
            <p className="text-[10px] text-slate-400">Enforce verified literature citations</p>
          </div>
          <input
            type="checkbox"
            checked={enforceRAG}
            onChange={(e) => setEnforceRAG(e.target.checked)}
            className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="pt-2 border-t border-slate-800">
        <Button variant="primary" className="w-full" onClick={toggleControlDrawer}>
          Apply Settings
        </Button>
      </div>
    </div>
  );
}
