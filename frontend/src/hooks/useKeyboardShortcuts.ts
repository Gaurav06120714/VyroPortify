"use client";

import { useEffect } from "react";

export interface Shortcut {
  
  key: string;
  
  mod?: boolean;   
  shift?: boolean;
  alt?: boolean;
  description?: string;
  handler: (e: KeyboardEvent) => void;
}

const isMac =
  typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);

function matches(e: KeyboardEvent, s: Shortcut): boolean {
  
  if (!e.key || typeof e.key !== "string") return false;
  if (e.key.toLowerCase() !== s.key.toLowerCase()) return false;
  const mod = isMac ? e.metaKey : e.ctrlKey;
  if (s.mod !== undefined && mod !== s.mod) return false;
  if (s.shift !== undefined && e.shiftKey !== s.shift) return false;
  if (s.alt !== undefined && e.altKey !== s.alt) return false;
  return true;
}

function shouldIgnoreEvent(e: KeyboardEvent, s: Shortcut): boolean {
  const t = e.target as HTMLElement | null;
  if (!t) return false;
  const tag = t.tagName;
  const editable =
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT" ||
    t.isContentEditable;
  if (!editable) return false;
  
  return !s.mod;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      for (const s of shortcuts) {
        if (!matches(e, s)) continue;
        if (shouldIgnoreEvent(e, s)) continue;
        e.preventDefault();
        s.handler(e);
        return;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [shortcuts]);
}

export function modKeyLabel(): string {
  return isMac ? "⌘" : "Ctrl";
}
