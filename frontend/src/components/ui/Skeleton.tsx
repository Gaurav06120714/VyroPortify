"use client";

import React from "react";
import { useTheme } from "@/context/ThemeContext";
import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({ className, style }: SkeletonProps) {
  const { isLight } = useTheme();
  return (
    <div
      className={cn("animate-pulse rounded-lg", className)}
      style={{
        ...style,
        background: isLight
          ? "linear-gradient(90deg, var(--pf-text) 25%, #f0f0f7 50%, var(--pf-text) 75%)"
          : "linear-gradient(90deg, #1a1a2e 25%, #232340 50%, #1a1a2e 75%)",
        backgroundSize: "200% 100%",
        animation: "skeleton-shimmer 1.5s infinite",
      }}
    />
  );
}

export function PortfolioCardSkeleton() {
  return (
    <div className="rounded-2xl border border-[var(--pf-border-dim)] bg-[var(--pf-surface)] p-5 space-y-4">
      <Skeleton className="h-36 w-full rounded-xl" />
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
      <div className="flex gap-2 pt-1">
        <Skeleton className="h-8 w-20 rounded-lg" />
        <Skeleton className="h-8 w-20 rounded-lg" />
      </div>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-[var(--pf-border-dim)] bg-[var(--pf-surface)] p-5 space-y-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
}

export function BillingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[var(--pf-border-dim)] bg-[var(--pf-surface)] p-6 space-y-4">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-4 w-64" />
        <Skeleton className="h-10 w-40 rounded-xl" />
      </div>
      <div className="rounded-xl border border-[var(--pf-border-dim)] bg-[var(--pf-surface)] p-6 space-y-3">
        <Skeleton className="h-5 w-24" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex justify-between items-center py-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function ResumeListSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="flex items-center gap-4 rounded-xl border border-[var(--pf-border-dim)] bg-[var(--pf-surface)] p-4"
        >
          <Skeleton className="h-10 w-10 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-8 w-24 rounded-lg" />
        </div>
      ))}
    </div>
  );
}

export function TableRowSkeleton({ cols = 4 }: { cols?: number }) {
  return (
    <div className="flex items-center gap-4 px-4 py-3 border-b border-[var(--pf-border-subtle)]">
      {Array.from({ length: cols }).map((_, i) => (
        <Skeleton key={i} className="h-4 flex-1" style={{ maxWidth: i === 0 ? 200 : undefined }} />
      ))}
    </div>
  );
}
