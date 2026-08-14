import * as React from "react";
import { cn } from "@/lib/utils";

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  name?: string;
  src?: string;
  size?: "sm" | "md" | "lg";
}

export function Avatar({ name = "User", src, size = "md", className, ...props }: AvatarProps) {
  const initials = name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const sizeClasses = {
    sm: "h-8 w-8 text-xs",
    md: "h-10 w-10 text-sm",
    lg: "h-12 w-12 text-base",
  };

  return (
    <div
      className={cn(
        "relative flex shrink-0 overflow-hidden rounded-full border border-border bg-secondary font-semibold text-secondary-foreground items-center justify-center shadow-inner",
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {src ? (
        <img src={src} alt={name} className="aspect-square h-full w-full object-cover" />
      ) : (
        <span>{initials}</span>
      )}
    </div>
  );
}
