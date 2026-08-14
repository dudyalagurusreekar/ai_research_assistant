"use client";

import React, { useState } from "react";
import { ChatMessage as ChatMessageType } from "@/store/use-chat-store";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import {
  BrainCircuit,
  User,
  Cpu,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.sender_type === "USER";
  const isTool = message.sender_type === "TOOL";
  const [copied, setCopied] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);

  const handleCopyCode = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "flex gap-4 p-5 rounded-2xl transition-all duration-200 animate-fade-in",
        isUser
          ? "bg-indigo-600/10 border border-indigo-500/20 ml-8 sm:ml-16"
          : isTool
          ? "bg-slate-900/60 border border-slate-800"
          : "glass-card border border-slate-200/60 dark:border-slate-800/80 mr-4 sm:mr-12 shadow-glass-sm"
      )}
    >
      {/* Sender Avatar */}
      <div
        className={cn(
          "w-9 h-9 rounded-xl flex items-center justify-center text-white shrink-0 font-bold shadow-sm",
          isUser
            ? "bg-gradient-to-br from-indigo-500 to-indigo-700"
            : isTool
            ? "bg-slate-800 text-slate-400 border border-slate-700"
            : "bg-gradient-to-br from-indigo-600 via-indigo-500 to-cyan-500 shadow-glow-indigo"
        )}
      >
        {isUser ? <User className="w-5 h-5" /> : isTool ? <Cpu className="w-5 h-5" /> : <BrainCircuit className="w-5 h-5" />}
      </div>

      {/* Message Content & Controls */}
      <div className="flex-1 space-y-3 min-w-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-extrabold tracking-wide uppercase text-slate-900 dark:text-slate-100">
              {isUser ? "You" : isTool ? "Tool Execution" : "ARA Research Assistant"}
            </span>
            <span className="text-[10px] text-slate-400">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>

          {!isUser && message.confidence_score && (
            <div className="flex items-center gap-1.5">
              <Badge variant="success" className="gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                <span>{(message.confidence_score * 100).toFixed(0)}% Grounded</span>
              </Badge>
            </div>
          )}
        </div>

        {/* Expandable Agent Reasoning Steps */}
        {!isUser && message.reasoning_steps && message.reasoning_steps.length > 0 && (
          <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 overflow-hidden text-xs">
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              className="flex items-center justify-between w-full px-3.5 py-2 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <div className="flex items-center gap-1.5 font-mono text-[11px] font-semibold text-indigo-400">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Agent Execution Timeline ({message.reasoning_steps.length} steps)</span>
              </div>
              {showReasoning ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showReasoning && (
              <div className="px-3.5 py-2.5 border-t border-slate-800/80 space-y-1.5 bg-slate-950/40">
                {message.reasoning_steps.map((step) => (
                  <div key={step.id} className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-300 font-medium">{step.title}</span>
                    <Badge variant="success" size="sm">{step.status}</Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Text Content */}
        <div className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed space-y-2 whitespace-pre-wrap">
          {message.content.split("\n").map((line, lineIdx) => {
            // Process bold formatting **text**
            const parts = line.split(/(\*\*.*?\*\*)/g);
            return (
              <div key={lineIdx} className={line.startsWith("- ") || line.match(/^\d+\./) ? "pl-2 border-l-2 border-indigo-500/40 my-1" : ""}>
                {parts.map((part, partIdx) => {
                  if (part.startsWith("**") && part.endsWith("**")) {
                    return (
                      <strong key={partIdx} className="font-extrabold text-indigo-400 dark:text-indigo-300">
                        {part.slice(2, -2)}
                      </strong>
                    );
                  }
                  return <span key={partIdx}>{part}</span>;
                })}
              </div>
            );
          })}
        </div>

        {/* Code Snippet Action Header */}
        {!isUser && message.content.includes("```") && (
          <div className="flex justify-end pt-1">
            <button
              onClick={() => handleCopyCode(message.content)}
              className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-indigo-400 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy Code"}</span>
            </button>
          </div>
        )}

        {/* Citations Footer */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="pt-2 border-t border-slate-200/50 dark:border-slate-800/60 space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Verified Literature Citations
            </span>
            <div className="flex flex-wrap gap-2">
              {message.citations.map((cit, i) => (
                <div
                  key={cit.id}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px] font-mono hover:bg-indigo-500/20 transition-colors"
                  title={cit.snippet}
                >
                  <span>[{i + 1}] {cit.source_title}</span>
                  {cit.doi && <ExternalLink className="w-3 h-3 opacity-75" />}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
