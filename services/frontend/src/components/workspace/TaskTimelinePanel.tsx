"use client";

import { useResearchStore } from "@/stores/researchStore";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Clock, Play, Wrench, ChevronRight } from "lucide-react";

export function TaskTimelinePanel() {
  const { currentPlan } = useResearchStore();

  if (!currentPlan) {
    return (
      <Card className="glass-panel h-full flex flex-col justify-center items-center text-center p-6">
        <Clock className="h-8 w-8 text-muted-foreground mb-2" />
        <CardTitle className="text-sm font-semibold">No DAG Execution Active</CardTitle>
        <CardDescription className="text-xs">
          Submit a research query to generate and visualize parallel task execution waves.
        </CardDescription>
      </Card>
    );
  }

  return (
    <Card className="glass-panel h-full flex flex-col overflow-hidden">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Play className="h-4 w-4 text-primary" /> Task DAG Timeline
          </CardTitle>
          <Badge variant="running">
            Complexity: {currentPlan.complexity_score || 5}/10
          </Badge>
        </div>
        <CardDescription className="text-[11px]">
          Plan ID: <span className="font-mono text-primary">{currentPlan.plan_id}</span>
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {currentPlan.execution_waves.map((wave, waveIdx) => (
          <div key={waveIdx} className="space-y-2 border-l-2 border-primary/40 pl-3 relative">
            <div className="flex items-center gap-2 text-xs font-semibold text-primary">
              <span>Wave {waveIdx + 1}</span>
              <span className="text-[10px] text-muted-foreground">({wave.length} subtask)</span>
            </div>

            <div className="space-y-2">
              {wave.map((tid) => {
                const subtask = currentPlan.sub_tasks.find((t) => t.task_id === tid);
                const status = subtask?.status || "completed";

                return (
                  <div
                    key={tid}
                    className="rounded-lg border border-border/60 bg-secondary/30 p-2.5 space-y-1 hover:border-primary/30 transition-colors text-xs"
                  >
                    <div className="flex items-start justify-between">
                      <span className="font-medium text-foreground">{subtask?.title || tid}</span>
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border/40">
                      <span className="flex items-center gap-1">
                        <Wrench className="h-3 w-3 text-primary" /> {subtask?.task_type || "general_qa"}
                      </span>
                      <span className="font-mono">{tid}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
