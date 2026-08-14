"use client";

import React, { useState } from "react";
import { ActionType, WorkflowStep, useBrowserStore } from "@/store/use-browser-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Play, Plus, Trash2, Cpu, CheckCircle2 } from "lucide-react";
import { useUIStore } from "@/store/use-ui-store";
import { browserService } from "../services/browser-service";

export function WorkflowBuilder() {
  const { workflowSteps, addWorkflowStep, setIsExecuting, setStatus, addLog, addExtractedData, sessionId } =
    useBrowserStore();
  const { addToast } = useUIStore();

  const [action, setAction] = useState<ActionType>("NAVIGATE");
  const [target, setTarget] = useState("");
  const [value, setValue] = useState("");

  const handleAddStep = (e: React.FormEvent) => {
    e.preventDefault();
    addWorkflowStep({
      id: `step_${Date.now()}`,
      action,
      target: target || undefined,
      value: value || undefined,
      status: "pending",
    });
    setTarget("");
    setValue("");
  };

  const handleExecuteWorkflow = async () => {
    setIsExecuting(true);
    setStatus("running");
    addLog(`[START] Executing browser automation sequence (${workflowSteps.length} steps)...`);
    addToast({ type: "info", title: "Workflow Execution Started", message: "Playwright automating browser session..." });

    for (let i = 0; i < workflowSteps.length; i++) {
      const s = workflowSteps[i];
      addLog(`[STEP ${i + 1}] Action: ${s.action} -> Target: ${s.target || "N/A"}`);
      await new Promise((resolve) => setTimeout(resolve, 800));
    }

    const extracted = await browserService.executeWorkflow(sessionId || "brw_session_001", workflowSteps);
    addExtractedData(extracted);
    addLog("[SUCCESS] Extracted literature entries cleanly into JSON");

    setIsExecuting(false);
    setStatus("completed");
    addToast({ type: "success", title: "Workflow Complete", message: "Extracted data saved cleanly." });
  };

  return (
    <Card variant="glass" className="space-y-4">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            Automation Workflow Builder
          </CardTitle>
          <CardDescription>Design drag-and-drop Playwright execution sequences</CardDescription>
        </div>

        <Button variant="primary" onClick={handleExecuteWorkflow} leftIcon={<Play className="w-4 h-4 fill-current" />}>
          Run Automation Sequence
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Step Input Bar */}
        <form onSubmit={handleAddStep} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <select
            value={action}
            onChange={(e) => setAction(e.target.value as ActionType)}
            className="text-xs font-semibold p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100"
          >
            <option value="NAVIGATE">NAVIGATE</option>
            <option value="CLICK_ELEMENT">CLICK_ELEMENT</option>
            <option value="TYPE_TEXT">TYPE_TEXT</option>
            <option value="EXTRACT_TABLE">EXTRACT_TABLE</option>
            <option value="DOWNLOAD_PDF">DOWNLOAD_PDF</option>
            <option value="CAPTURE_SCREENSHOT">CAPTURE_SCREENSHOT</option>
          </select>

          <Input
            placeholder="Target CSS / URL..."
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          />

          <Input
            placeholder="Optional value / text..."
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />

          <Button type="submit" variant="outline" leftIcon={<Plus className="w-4 h-4" />}>
            Add Step
          </Button>
        </form>

        {/* Steps List */}
        <div className="space-y-2 pt-2">
          {workflowSteps.map((step, idx) => (
            <div
              key={step.id}
              className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800"
            >
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-indigo-600/20 text-indigo-400 font-bold text-xs flex items-center justify-center">
                  {idx + 1}
                </span>
                <span className="text-xs font-bold text-slate-100 font-mono">{step.action}</span>
                {step.target && <span className="text-xs text-slate-400 font-mono">Target: {step.target}</span>}
              </div>

              <Badge variant={step.status === "completed" ? "success" : "neutral"}>{step.status}</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
