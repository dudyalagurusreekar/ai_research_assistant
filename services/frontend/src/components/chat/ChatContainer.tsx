"use client";

import { useResearchStore } from "@/stores/researchStore";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { CitationCard } from "@/components/chat/CitationCard";
import { useRef, useEffect } from "react";
import { Sparkles, Bot, FlaskConical, Network, Scale } from "lucide-react";

const SUGGESTED_PROMPTS = [
  {
    title: "CRISPR Off-Target Analysis",
    query: "Synthesize latest findings on CRISPR-Cas9 vs Cas12a off-target specificity and list contradictory claims.",
    icon: FlaskConical,
  },
  {
    title: "GraphRAG Entity Reasoning",
    query: "Extract knowledge graph entities for Alzheimer amyloid-beta therapies and identify contradiction edges.",
    icon: Network,
  },
  {
    title: "MCDA Pareto Trade-Off",
    query: "Run MCDA trade-off model evaluating Solid-State vs Lithium-Sulfur battery chemistries.",
    icon: Scale,
  },
];

export function ChatContainer({ onSendMessage }: { onSendMessage: (query: string) => void }) {
  const { messages, activeCitation } = useResearchStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-full flex-col justify-between overflow-hidden relative">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 pr-2">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Suggested Prompts if short thread */}
      {messages.length <= 2 && (
        <div className="px-4 pb-2">
          <p className="text-[11px] font-semibold text-muted-foreground mb-2 flex items-center gap-1">
            <Sparkles className="h-3.5 w-3.5 text-primary" /> Suggested Enterprise Workflows
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {SUGGESTED_PROMPTS.map((p) => {
              const Icon = p.icon;
              return (
                <button
                  key={p.title}
                  onClick={() => onSendMessage(p.query)}
                  className="flex flex-col items-start gap-1 rounded-lg border border-border/60 bg-secondary/30 p-2.5 text-left hover:border-primary/40 hover:bg-secondary/60 transition-all group"
                >
                  <div className="flex items-center gap-1.5 font-semibold text-xs text-foreground group-hover:text-primary">
                    <Icon className="h-3.5 w-3.5 text-primary shrink-0" /> {p.title}
                  </div>
                  <p className="text-[10px] text-muted-foreground line-clamp-2">{p.query}</p>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Input Form */}
      <div className="p-4 border-t border-border/50 bg-card/40 backdrop-blur-xl">
        <ChatInput onSendMessage={onSendMessage} />
      </div>

      {/* Citation Modal / Drawer if selected */}
      {activeCitation && <CitationCard citation={activeCitation} />}
    </div>
  );
}
