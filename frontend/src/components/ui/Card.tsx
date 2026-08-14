import React, { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "glass" | "solid" | "outline";
}

export function Card({ className, variant = "glass", children, ...props }: CardProps) {
  const variants = {
    glass: "glass-card shadow-glass-sm",
    solid: "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm",
    outline: "bg-transparent border border-slate-300 dark:border-slate-800",
  };

  return (
    <div className={cn("rounded-2xl p-6 transition-all duration-200", variants[variant], className)} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("space-y-1 mb-4", className)} {...props}>{children}</div>;
}

export function CardTitle({ className, children, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100", className)} {...props}>{children}</h3>;
}

export function CardDescription({ className, children, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-xs text-slate-500 dark:text-slate-400", className)} {...props}>{children}</p>;
}

export function CardContent({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("", className)} {...props}>{children}</div>;
}
