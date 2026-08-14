import React, { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "glass";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      children,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      leftIcon,
      rightIcon,
      type = "button",
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none active:scale-[0.98]";

    const variants = {
      primary:
        "bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-glow-indigo focus:ring-indigo-500 border border-indigo-500/30",
      secondary:
        "bg-slate-800 hover:bg-slate-700 text-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 focus:ring-slate-500 border border-slate-700",
      outline:
        "border border-slate-300 dark:border-slate-700 bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-200 focus:ring-indigo-500",
      ghost:
        "bg-transparent hover:bg-slate-200/50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300 focus:ring-indigo-500",
      danger:
        "bg-rose-600 hover:bg-rose-500 text-white focus:ring-rose-500 shadow-sm border border-rose-500/30",
      glass:
        "glass-panel hover:bg-white/90 dark:hover:bg-slate-800/90 text-slate-800 dark:text-slate-100 focus:ring-indigo-500 shadow-glass-sm",
    };

    const sizes = {
      sm: "text-xs px-3 py-1.5 gap-1.5 min-h-[32px]",
      md: "text-sm px-4 py-2 gap-2 min-h-[40px]",
      lg: "text-base px-6 py-3 gap-2.5 min-h-[48px]",
    };

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        ) : leftIcon ? (
          <span className="shrink-0">{leftIcon}</span>
        ) : null}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";
