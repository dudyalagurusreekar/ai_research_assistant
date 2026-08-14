"use client";

import React, { useState } from "react";
import { useKnowledgeStore } from "@/store/use-knowledge-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Brain, Plus, Trash2, ShieldCheck, Clock } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";

export function LongTermMemoryView() {
  const { memories, addMemory, deleteMemory } = useKnowledgeStore();
  const { addToast } = useUIStore();

  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [category, setCategory] = useState<"USER_PREFERENCE" | "PROJECT_CONTEXT" | "EPISODIC_EXECUTION">("USER_PREFERENCE");

  const handleAddMemory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim() || !value.trim()) return;

    addMemory({
      id: `mem_${Date.now()}`,
      category,
      key,
      value,
      retention_policy: "PERMANENT",
      created_at: new Date().toISOString(),
    });
    setKey("");
    setValue("");
    addToast({ type: "success", title: "Memory Stored", message: `Saved "${key}" to Long-Term Memory.` });
  };

  return (
    <div className="space-y-6">
      {/* Add Memory Input Form */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-400" />
            Store Memory Attribute
          </CardTitle>
          <CardDescription>Persistent semantic memory across sessions and agent workflows</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddMemory} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as any)}
              className="text-xs font-semibold p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100"
            >
              <option value="USER_PREFERENCE">User Preference</option>
              <option value="PROJECT_CONTEXT">Project Context</option>
              <option value="EPISODIC_EXECUTION">Episodic Execution</option>
            </select>

            <Input placeholder="Memory Key (e.g. preferred_model)..." value={key} onChange={(e) => setKey(e.target.value)} />
            <Input placeholder="Memory Value..." value={value} onChange={(e) => setValue(e.target.value)} />

            <Button type="submit" variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
              Save Memory
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Memory List */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle>Persisted Long-Term Memory Platform ({memories.length})</CardTitle>
          <CardDescription>Configurable retention policies and privacy controls</CardDescription>
        </CardHeader>

        <CardContent className="space-y-3">
          {memories.map((mem) => (
            <div
              key={mem.id}
              className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant="brand">{mem.category}</Badge>
                  <span className="text-xs font-bold text-indigo-400 font-mono">{mem.key}</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-mono">{mem.value}</p>
                <span className="text-[10px] text-slate-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Retention: {mem.retention_policy}
                </span>
              </div>

              <button
                onClick={() => deleteMemory(mem.id)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 transition-colors"
                title="Purge Memory Item"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
