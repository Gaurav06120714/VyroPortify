"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import type { SaveStatus } from "@/hooks/useDebouncedSave";
import { cn } from "@/lib/utils";

interface Props {
  status: SaveStatus;
  lastSavedAt: Date | null;
  errorMessage?: string | null;
}

export function SaveStatusPill({ status, lastSavedAt, errorMessage }: Props) {
  const [, force] = useState(0);

  useEffect(() => {
    if (status !== "saved" || !lastSavedAt) return;
    const id = setInterval(() => force((n) => n + 1), 30_000);
    return () => clearInterval(id);
  }, [status, lastSavedAt]);

  if (status === "saving") {
    return (
      <Badge>
        <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--pf-accent)]" />
        Saving…
      </Badge>
    );
  }

  if (status === "error") {
    return (
      <Badge tone="error" title={errorMessage ?? undefined}>
        <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
        Save failed
      </Badge>
    );
  }

  if (status === "saved" && lastSavedAt) {
    return (
      <Badge>
        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
        Saved · {relativeTime(lastSavedAt)}
      </Badge>
    );
  }

  return null;
}

function Badge({
  children,
  tone,
  title,
}: {
  children: React.ReactNode;
  tone?: "error";
  title?: string;
}) {
  return (
    <span
      title={title}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs",
        tone === "error"
          ? "bg-red-500/10 text-red-600"
          : "bg-[var(--pf-surface2)] text-[var(--pf-muted)]",
      )}
    >
      {children}
    </span>
  );
}

function relativeTime(d: Date): string {
  const seconds = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}
