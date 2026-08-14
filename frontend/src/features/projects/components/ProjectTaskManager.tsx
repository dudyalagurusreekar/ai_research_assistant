"use client";

import React, { useState } from "react";
import { ProjectTask, useProjectStore } from "@/store/use-project-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Plus, CheckSquare, Clock, ArrowRight, ArrowLeft } from "lucide-react";

export function ProjectTaskManager({ projectId }: { projectId: string }) {
  const { tasks, addTask, updateTaskStatus } = useProjectStore();
  const [newTitle, setNewTitle] = useState("");
  const [priority, setPriority] = useState<"high" | "medium" | "low">("medium");

  const projectTasks = tasks.filter((t) => t.project_id === projectId);

  const handleAddTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    addTask({
      id: `tsk_${Date.now()}`,
      project_id: projectId,
      title: newTitle,
      status: "todo",
      priority: priority,
    });
    setNewTitle("");
  };

  const todoTasks = projectTasks.filter((t) => t.status === "todo");
  const inProgressTasks = projectTasks.filter((t) => t.status === "in_progress");
  const doneTasks = projectTasks.filter((t) => t.status === "done");

  return (
    <div className="space-y-6">
      {/* Add Task Input Bar */}
      <form onSubmit={handleAddTask} className="flex gap-3">
        <Input
          placeholder="Add a new research task..."
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          className="flex-1"
        />
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value as any)}
          className="text-xs font-semibold p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200"
        >
          <option value="high">High Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>
        <Button type="submit" variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
          Add Task
        </Button>
      </form>

      {/* KanBan Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Todo Column */}
        <Card variant="glass">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-amber-400">To Do</CardTitle>
              <Badge variant="warning">{todoTasks.length}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {todoTasks.map((t) => (
              <TaskCard key={t.id} task={t} onMove={(st) => updateTaskStatus(t.id, st)} />
            ))}
          </CardContent>
        </Card>

        {/* In Progress Column */}
        <Card variant="glass">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-indigo-400">In Progress</CardTitle>
              <Badge variant="brand">{inProgressTasks.length}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {inProgressTasks.map((t) => (
              <TaskCard key={t.id} task={t} onMove={(st) => updateTaskStatus(t.id, st)} />
            ))}
          </CardContent>
        </Card>

        {/* Done Column */}
        <Card variant="glass">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-emerald-400">Completed</CardTitle>
              <Badge variant="success">{doneTasks.length}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {doneTasks.map((t) => (
              <TaskCard key={t.id} task={t} onMove={(st) => updateTaskStatus(t.id, st)} />
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TaskCard({
  task,
  onMove,
}: {
  task: ProjectTask;
  onMove: (status: "todo" | "in_progress" | "done") => void;
}) {
  return (
    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-slate-700 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-100">{task.title}</span>
        <Badge
          variant={task.priority === "high" ? "error" : task.priority === "medium" ? "info" : "neutral"}
          size="sm"
        >
          {task.priority}
        </Badge>
      </div>

      <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400">
        {task.status !== "todo" && (
          <button
            onClick={() => onMove(task.status === "done" ? "in_progress" : "todo")}
            className="hover:text-slate-200 flex items-center gap-1 font-semibold"
          >
            <ArrowLeft className="w-3 h-3" /> Back
          </button>
        )}
        {task.status !== "done" && (
          <button
            onClick={() => onMove(task.status === "todo" ? "in_progress" : "done")}
            className="hover:text-indigo-400 flex items-center gap-1 font-semibold ml-auto"
          >
            Advance <ArrowRight className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
}
