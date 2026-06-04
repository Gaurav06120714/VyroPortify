"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { useKeyboardShortcuts, modKeyLabel } from "@/hooks/useKeyboardShortcuts";
import { cn } from "@/lib/utils";

interface Command {
  id: string;
  title: string;
  hint?: string;
  // Either a route to navigate to or a custom action.
  href?: string;
  action?: () => void;
  keywords?: string[];
}

const DEFAULT_COMMANDS: Command[] = [
  { id: "go-dashboard", title: "Go to Dashboard", href: "/dashboard" },
  { id: "go-portfolios", title: "View Portfolios", href: "/dashboard/portfolios" },
  { id: "go-templates", title: "Browse Templates", href: "/dashboard/templates" },
  { id: "go-build", title: "Build Resume", href: "/dashboard/build-resume" },
  { id: "go-upload", title: "Upload Resume", href: "/dashboard/upload" },
  { id: "go-cover", title: "Write Cover Letter", href: "/dashboard/cover-letter" },
  { id: "go-analytics", title: "Open Analytics", href: "/dashboard/analytics" },
  { id: "go-settings", title: "Account Settings", href: "/dashboard/settings" },
  { id: "go-billing", title: "Billing", href: "/dashboard/settings/billing" },
];

function score(cmd: Command, q: string): number {
  if (!q) return 1;
  const needle = q.toLowerCase();
  const hay = [cmd.title, ...(cmd.keywords ?? [])].join(" ").toLowerCase();
  if (hay.startsWith(needle)) return 3;
  if (hay.includes(" " + needle)) return 2;
  if (hay.includes(needle)) return 1;
  return 0;
}

// Lightweight Cmd-K palette. Avoids the cmdk dep — we only need a filtered
// list, keyboard nav, and Enter to fire. The shortcut to open is registered
// globally; the palette itself owns ↑/↓/Enter/Escape while open.
export function CommandPalette({ extra = [] }: { extra?: Command[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands = useMemo(() => [...DEFAULT_COMMANDS, ...extra], [extra]);

  const filtered = useMemo(() => {
    return commands
      .map((c) => ({ c, s: score(c, q) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s)
      .map((x) => x.c);
  }, [commands, q]);

  useKeyboardShortcuts([
    { key: "k", mod: true, handler: () => setOpen((v) => !v), description: "Open command palette" },
  ]);

  useEffect(() => {
    if (open) {
      setQ("");
      setActiveIdx(0);
      // Defer focus so the dialog has mounted.
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIdx((i) => Math.min(i + 1, filtered.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIdx((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        const cmd = filtered[activeIdx];
        if (cmd) runCommand(cmd);
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [open, activeIdx, filtered]);

  function runCommand(cmd: Command) {
    setOpen(false);
    if (cmd.action) cmd.action();
    else if (cmd.href) router.push(cmd.href);
  }

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      className="fixed inset-0 z-[var(--pf-z-modal)] flex items-start justify-center pt-[12vh] px-4"
      onClick={() => setOpen(false)}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-xl rounded-2xl border border-[var(--pf-border-light)]
                   bg-[var(--pf-surface)] shadow-[var(--pf-elev-4)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b border-[var(--pf-border-subtle)] px-4">
          <Search className="h-4 w-4 text-[var(--pf-muted)]" aria-hidden />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setActiveIdx(0);
            }}
            placeholder="Search commands…"
            className="h-12 w-full bg-transparent text-sm text-[var(--pf-text)]
                       placeholder:text-[var(--pf-muted)] focus:outline-none"
          />
          <kbd className="hidden md:inline-block rounded border border-[var(--pf-border-light)]
                          px-1.5 py-0.5 text-[10px] text-[var(--pf-muted)]">
            ESC
          </kbd>
        </div>
        <ul role="listbox" className="max-h-80 overflow-y-auto py-2">
          {filtered.length === 0 && (
            <li className="px-4 py-6 text-center text-sm text-[var(--pf-muted)]">
              No results
            </li>
          )}
          {filtered.map((c, i) => (
            <li
              key={c.id}
              role="option"
              aria-selected={i === activeIdx}
              onMouseEnter={() => setActiveIdx(i)}
              onClick={() => runCommand(c)}
              className={cn(
                "flex cursor-pointer items-center justify-between px-4 py-2 text-sm",
                i === activeIdx
                  ? "bg-[var(--pf-accent-subtle)] text-[var(--pf-text)]"
                  : "text-[var(--pf-text-dim)]",
              )}
            >
              <span>{c.title}</span>
              {c.hint && (
                <span className="text-xs text-[var(--pf-muted)]">{c.hint}</span>
              )}
            </li>
          ))}
        </ul>
        <div className="flex items-center justify-between border-t border-[var(--pf-border-subtle)] px-4 py-2 text-[11px] text-[var(--pf-muted)]">
          <span>
            <kbd>↑</kbd> <kbd>↓</kbd> navigate · <kbd>↵</kbd> select
          </span>
          <span>
            <kbd>{modKeyLabel()}</kbd>+<kbd>K</kbd> toggle
          </span>
        </div>
      </div>
    </div>
  );
}
