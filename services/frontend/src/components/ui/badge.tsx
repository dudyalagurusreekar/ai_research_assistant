import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "success" | "running" | "warning" | "error" | "neutral" | "outline";
}

export function Badge({ className, variant = "neutral", ...props }: BadgeProps) {
  const variants = {
    success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 dark:text-emerald-300",
    running: "border-sky-500/30 bg-sky-500/10 text-sky-400 dark:text-sky-300 animate-pulse",
    warning: "border-amber-500/30 bg-amber-500/10 text-amber-400 dark:text-amber-300",
    error: "border-rose-500/30 bg-rose-500/10 text-rose-400 dark:text-rose-300",
    neutral: "border-border bg-secondary text-secondary-foreground",
    outline: "border-border text-foreground",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
