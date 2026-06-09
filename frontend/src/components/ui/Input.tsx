"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-10 w-full rounded-xl border border-[var(--pf-border-light)] " +
          "bg-[var(--pf-surface)] px-3 text-sm text-[var(--pf-text)] " +
          "placeholder:text-[var(--pf-muted)] " +
          "focus:border-[var(--pf-accent)] focus:outline-none transition-colors " +
          "disabled:opacity-50 disabled:cursor-not-allowed",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
