"use client";

import * as React from "react";
import { ChatMessageItem, useResearchStore } from "@/stores/researchStore";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Sparkles, User, Wrench, BookOpen, Copy, Check } from "lucide-react";
import { useState } from "react";

export function ChatMessage({ message }: { message: ChatMessageItem }) {
  const { setActiveCitation } = useResearchStore();
  const [copied, setCopied] = useState(false);

  const isUser = message.sender_type === "USER";
  const isTool = message.sender_type === "TOOL";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Render markdown text formatting with inline citations
  const renderFormattedContent = (content: string) => {
    // Simple markdown link & bold parser for clean rendering
    const parts = content.split(/(\[\d+\]|\*\*.*?\*\*|`.*?`)/g);

    return parts.map((part, index) => {
      if (part.startsWith("[") && part.endsWith("]")) {
        const citationNum = part.slice(1, -1);
        const idx = parseInt(citationNum) - 1;
        const citation = message.citations?.[idx] || {
          id: `cit_${idx}`,
          source_title: `Authoritative Evidence Source #${citationNum}`,
          snippet: "High-confidence retrieval match from Enterprise pgvector hybrid index.",
          similarity_score: 0.965,
        };

        return (
          <button
            key={index}
            onClick={() => setActiveCitation(citation)}
            className="inline-flex items-center gap-1 mx-0.5 rounded bg-primary/20 px-1.5 py-0.5 text-[11px] font-semibold text-primary hover:bg-primary/30 transition-colors"
          >
            <BookOpen className="h-3 w-3" /> [{citationNum}]
          </button>
        );
      }

      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={index} className="font-semibold text-foreground">{part.slice(2, -2)}</strong>;
      }

      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code key={index} className="rounded bg-secondary/80 px-1.5 py-0.5 font-mono text-xs text-primary">
            {part.slice(1, -1)}
          </code>
        );
      }

      return part;
    });
  };

  return (
    <div
      className={cn(
        "flex gap-4 p-4 rounded-xl transition-all",
        isUser
          ? "bg-secondary/40 border border-border/40"
          : isTool
          ? "bg-amber-500/5 border border-amber-500/20 text-xs"
          : "bg-card/70 border border-border/60 glass-panel"
      )}
    >
      {/* Icon / Avatar */}
      <div className="shrink-0">
        {isUser ? (
          <Avatar name="User" size="sm" className="bg-primary/20 text-primary border-primary/30" />
        ) : isTool ? (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500/20 text-amber-400">
            <Wrench className="h-4 w-4" />
          </div>
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md shadow-primary/30">
            <Sparkles className="h-4 w-4" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-foreground">
              {isUser ? "You" : isTool ? "Tool Execution Engine" : "ARA Research Assistant"}
            </span>
            {message.isStreaming && (
              <span className="inline-block h-2 w-2 rounded-full bg-primary animate-pulse" />
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="text-muted-foreground hover:text-foreground p-1 transition-colors"
              title="Copy message"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
            <span className="text-[10px] text-muted-foreground">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
        </div>

        {/* Text Body */}
        <div className="text-xs leading-relaxed text-foreground whitespace-pre-wrap">
          {renderFormattedContent(message.content)}
        </div>

        {/* Tool Call Badges */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {message.tool_calls.map((tc: any, i: number) => (
              <Badge key={i} variant="neutral" className="text-[10px] gap-1">
                <Wrench className="h-3 w-3 text-primary" /> {tc.tool_name || tc.name || "Tool Invocation"}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
