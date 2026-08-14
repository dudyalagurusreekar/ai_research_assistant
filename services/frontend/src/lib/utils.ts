import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string | Date): string {
  const date = typeof dateString === "string" ? new Date(dateString) : dateString;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function truncateString(str: string, maxLength: number = 50): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + "...";
}

export function getStatusBadgeVariant(status: string): "success" | "running" | "warning" | "error" | "neutral" {
  switch (status.toLowerCase()) {
    case "completed":
    case "success":
    case "active":
      return "success";
    case "running":
    case "in_progress":
    case "pending":
      return "running";
    case "degraded":
    case "warning":
      return "warning";
    case "failed":
    case "error":
      return "error";
    default:
      return "neutral";
  }
}
