"use client";

import React, { useState, useRef } from "react";
import { useChatStore } from "@/store/use-chat-store";
import { Button } from "@/components/ui/Button";
import { FileDropzone } from "./FileDropzone";
import { Send, Paperclip, Sliders, ShieldCheck, Sparkles } from "lucide-react";

export function ChatComposer({ onSendMessage }: { onSendMessage: (content: string) => void }) {
  const [prompt, setPrompt] = useState("");
  const { isStreaming, toggleControlDrawer, enforceRAG, setEnforceRAG, selectedModel, setSelectedModel } = useChatStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!prompt.trim() || isStreaming) return;
    onSendMessage(prompt);
    setPrompt("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="glass-card rounded-2xl p-3 border border-slate-200/80 dark:border-slate-800/80 shadow-2xl space-y-2">
      {/* File Dropzone Preview */}
      <FileDropzone />

      {/* Main Textarea Input */}
      <textarea
        ref={textareaRef}
        rows={2}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask ARA to research a topic, extract paper entities, or write Python code..."
        className="w-full bg-transparent text-xs sm:text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none resize-none px-2 py-1"
      />

      {/* Action Controls Bar */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-200/50 dark:border-slate-800/50">
        <div className="flex items-center gap-2">
          {/* Quick Model Selector */}
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="text-xs font-semibold bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-300 rounded-lg px-2.5 py-1.5 border border-slate-300 dark:border-slate-800 focus:outline-none"
          >
            <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
            <option value="ollama-local">Ollama Local (Offline)</option>
            <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
            <option value="gpt-4o">OpenAI GPT-4o</option>
          </select>

          {/* RAG Enforcement Toggle */}
          <button
            type="button"
            onClick={() => setEnforceRAG(!enforceRAG)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
              enforceRAG
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                : "bg-slate-100 dark:bg-slate-900 text-slate-400 border-slate-300 dark:border-slate-800"
            }`}
            title="Toggle RAG Citation Enforcement"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">RAG Citation Mode</span>
          </button>

          {/* Parameter Settings Trigger */}
          <button
            type="button"
            onClick={toggleControlDrawer}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="AI Parameter Drawer"
          >
            <Sliders className="w-4 h-4" />
          </button>
        </div>

        {/* Send Action Button */}
        <Button
          variant="primary"
          size="sm"
          isLoading={isStreaming}
          onClick={handleSend}
          disabled={!prompt.trim()}
          rightIcon={<Send className="w-3.5 h-3.5" />}
        >
          Send
        </Button>
      </div>
    </div>
  );
}
