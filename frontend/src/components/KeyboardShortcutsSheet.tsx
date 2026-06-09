"use client";

import { useState } from "react";
import { useKeyboardShortcuts, modKeyLabel } from "@/hooks/useKeyboardShortcuts";

interface ShortcutEntry {
  keys: string[];
  description: string;
}

const SHORTCUTS: ShortcutEntry[] = [
  { keys: [modKeyLabel(), "K"], description: "Open command palette" },
  { keys: ["?"], description: "Show this shortcut sheet" },
  { keys: ["G", "D"], description: "Go to Dashboard" },
  { keys: ["G", "P"], description: "Go to Portfolios" },
  { keys: ["G", "T"], description: "Go to Templates" },
  { keys: ["G", "S"], description: "Go to Settings" },
  { keys: ["Esc"], description: "Close any open dialog" },
];

export function KeyboardShortcutsSheet() {
  const [open, setOpen] = useState(false);

  useKeyboardShortcuts([
    { key: "?", shift: true, handler: () => setOpen((v) => !v) },
    { key: "/", handler: () => setOpen((v) => !v) },
  ]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      className="fixed inset-0 z-[var(--pf-z-modal)] flex items-center justify-center px-4"
      onClick={() => setOpen(false)}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-md rounded-2xl border border-[var(--pf-border-light)]
                   bg-[var(--pf-surface)] p-6 shadow-[var(--pf-elev-4)]"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold text-[var(--pf-text)]">
          Keyboard Shortcuts
        </h2>
        <p className="mt-1 text-sm text-[var(--pf-muted)]">
          Press <kbd>?</kbd> any time to open this sheet.
        </p>
        <dl className="mt-5 space-y-2">
          {SHORTCUTS.map((s) => (
            <div key={s.description} className="flex items-center justify-between text-sm">
              <dt className="text-[var(--pf-text-dim)]">{s.description}</dt>
              <dd className="flex items-center gap-1">
                {s.keys.map((k) => (
                  <kbd
                    key={k}
                    className="rounded border border-[var(--pf-border-light)]
                               bg-[var(--pf-surface2)] px-2 py-0.5 text-xs font-medium
                               text-[var(--pf-text)]"
                  >
                    {k}
                  </kbd>
                ))}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
