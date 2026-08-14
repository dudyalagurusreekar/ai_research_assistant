"use client";

import { useResearchStore } from "@/stores/researchStore";
import { Button } from "@/components/ui/button";
import { Send, Paperclip, Cpu, Sparkles, SlidersHorizontal } from "lucide-react";
import { useState } from "react";

export function ChatInput({ onSendMessage }: { onSendMessage: (query: string) => void }) {
  const [text, setText] = useState("");
  const { selectedModel, setSelectedModel, reasoningMode, setReasoningMode, isStreaming, isPlanning } = useResearchStore();
  const [showControls, setShowControls] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isStreaming || isPlanning) return;
    onSendMessage(text);
    setText("");
  };

  return (
    <div className="space-y-2">
      {/* Controls Bar */}
      <div className="flex items-center justify-between px-1 text-xs">
        <div className="flex items-center gap-2">
          {/* Model Selector */}
          <div className="flex items-center gap-1.5 rounded-lg border border-border bg-secondary/40 px-2.5 py-1">
            <Cpu className="h-3.5 w-3.5 text-primary" />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-transparent font-medium text-foreground focus:outline-none cursor-pointer"
            >
              <option value="gemini-2.5-pro" className="bg-card">Gemini 2.5 Pro (Advanced)</option>
              <option value="gemini-2.5-flash" className="bg-card">Gemini 2.5 Flash (Fast)</option>
              <option value="claude-3.5-sonnet" className="bg-card">Claude 3.5 Sonnet</option>
              <option value="gpt-4o" className="bg-card">GPT-4o Enterprise</option>
            </select>
          </div>

          {/* Reasoning Mode Toggle */}
          <div className="flex items-center gap-1.5 rounded-lg border border-border bg-secondary/40 px-2.5 py-1">
            <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            <select
              value={reasoningMode}
              onChange={(e) => setReasoningMode(e.target.value as any)}
              className="bg-transparent font-medium text-foreground focus:outline-none cursor-pointer capitalize"
            >
              <option value="standard" className="bg-card">Standard Reasoning</option>
              <option value="deep" className="bg-card">Deep MCDA Analysis</option>
              <option value="fast" className="bg-card">Fast Synthesis</option>
            </select>
          </div>
        </div>

        <button
          onClick={() => setShowControls(!showControls)}
          className="text-muted-foreground hover:text-foreground p-1 transition-colors"
          title="Toggle Controls"
        >
          <SlidersHorizontal className="h-4 w-4" />
        </button>
      </div>

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Ask ARA to analyze literature, construct GraphRAG memory, or execute decision models... (Shift+Enter for new line)"
          className="min-h-[60px] max-h-[160px] w-full resize-none rounded-xl border border-input bg-card/80 p-3.5 pr-24 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-all glass-panel"
        />

        <div className="absolute right-3 flex items-center gap-2">
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
            title="Attach Document"
          >
            <Paperclip className="h-4 w-4" />
          </button>
          <Button
            type="submit"
            size="icon"
            isLoading={isStreaming || isPlanning}
            disabled={!text.trim()}
            className="h-8 w-8 rounded-lg"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
