"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Check, ChevronRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChecklistItem {
  id: string;
  title: string;
  href: string;
}

const ITEMS: ChecklistItem[] = [
  { id: "upload", title: "Upload your first resume", href: "/dashboard/upload" },
  { id: "generate", title: "Generate a portfolio", href: "/dashboard/portfolios" },
  { id: "publish", title: "Publish & share the link", href: "/dashboard/portfolios" },
  { id: "template", title: "Try a different template", href: "/dashboard/templates" },
];

const STORAGE_KEY = "pf.onboarding.completed";

// Persistent first-run checklist. Stored client-side in localStorage so a
// user who completes step 1 doesn't see it un-check after a refresh.
// Server-driven completion can replace this later — for now the value is
// the activation nudge, not the audit trail.
export function OnboardingChecklist() {
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw === "__dismissed__") {
        setDismissed(true);
      } else if (raw) {
        setCompleted(new Set(JSON.parse(raw)));
      }
    } catch {
      /* ignore */
    }
  }, []);

  function toggle(id: string) {
    setCompleted((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
      } catch {
        /* ignore */
      }
      return next;
    });
  }

  function dismiss() {
    setDismissed(true);
    try {
      localStorage.setItem(STORAGE_KEY, "__dismissed__");
    } catch {
      /* ignore */
    }
  }

  if (dismissed) return null;
  const allDone = ITEMS.every((i) => completed.has(i.id));
  if (allDone) {
    // Auto-dismiss when complete — but only after a refresh, so the user
    // sees the win first.
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_KEY, "__dismissed__");
      } catch {}
    }
  }

  return (
    <div
      className="rounded-2xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)]
                 p-5 shadow-[var(--pf-elev-1)]"
      aria-label="Getting started checklist"
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-[var(--pf-accent)]" aria-hidden />
          <h2 className="text-sm font-semibold text-[var(--pf-text)]">
            Get started in 4 steps
          </h2>
        </div>
        <button
          onClick={dismiss}
          className="text-xs text-[var(--pf-muted)] hover:text-[var(--pf-text)]"
        >
          Dismiss
        </button>
      </div>
      <ul className="space-y-1">
        {ITEMS.map((item) => {
          const done = completed.has(item.id);
          return (
            <li key={item.id} className="group">
              <div className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-[var(--pf-surface2)]">
                <button
                  onClick={() => toggle(item.id)}
                  aria-pressed={done}
                  aria-label={`Mark "${item.title}" ${done ? "incomplete" : "complete"}`}
                  className={cn(
                    "flex h-5 w-5 items-center justify-center rounded-full border transition-colors",
                    done
                      ? "border-[var(--pf-accent)] bg-[var(--pf-accent)] text-white"
                      : "border-[var(--pf-border-medium)] text-transparent",
                  )}
                >
                  <Check className="h-3 w-3" />
                </button>
                <Link
                  href={item.href}
                  className={cn(
                    "flex flex-1 items-center justify-between text-sm",
                    done
                      ? "text-[var(--pf-muted)] line-through"
                      : "text-[var(--pf-text)]",
                  )}
                >
                  {item.title}
                  <ChevronRight className="h-4 w-4 opacity-0 transition-opacity group-hover:opacity-60" />
                </Link>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
