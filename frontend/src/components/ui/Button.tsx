"use client";

import { forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-semibold " +
    "transition-colors focus-visible:outline-none disabled:pointer-events-none " +
    "disabled:opacity-50 select-none",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--pf-accent)] text-white hover:bg-[var(--pf-accent-hover)] " +
          "shadow-[0_0_16px_var(--pf-border-hover)]",
        secondary:
          "bg-[var(--pf-surface)] text-[var(--pf-text)] border border-[var(--pf-border-light)] " +
          "hover:bg-[var(--pf-surface2)]",
        ghost:
          "bg-transparent text-[var(--pf-text)] hover:bg-[var(--pf-surface2)]",
        destructive: "bg-red-500 text-white hover:bg-red-600",
        link: "text-[var(--pf-accent)] underline-offset-4 hover:underline px-0 h-auto",
      },
      size: {
        sm: "h-8 px-3 text-sm rounded-lg",
        md: "h-10 px-4 text-sm rounded-xl",
        lg: "h-12 px-6 text-base rounded-xl",
        icon: "h-10 w-10 rounded-xl",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  ),
);
Button.displayName = "Button";

export { buttonVariants };
