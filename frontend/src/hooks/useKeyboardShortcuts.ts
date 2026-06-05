"use client";

import { useEffect } from "react";

export interface Shortcut {
  // Lower-cased key the listener compares against (e.g. "k", "?", "/").
  key: string;
  // Modifier keys — undefined means "don't care".
  mod?: boolean;   // Ctrl on Win/Linux, Cmd on macOS
  shift?: boolean;
  alt?: boolean;
  description?: string;
  handler: (e: KeyboardEvent) => void;
}

const isMac =
  typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);

function matches(e: KeyboardEvent, s: Shortcut): boolean {
  // Clerk's hosted SignIn/SignUp components dispatch synthetic key events
  // without `e.key` set (autofill, browser autocomplete on iOS). Guard
  // against that — without `key` the shortcut can't match anyway.
  if (!e.key || typeof e.key !== "string") return false;
  if (e.key.toLowerCase() !== s.key.toLowerCase()) return false;
  const mod = isMac ? e.metaKey : e.ctrlKey;
  if (s.mod !== undefined && mod !== s.mod) return false;
  if (s.shift !== undefined && e.shiftKey !== s.shift) return false;
  if (s.alt !== undefined && e.altKey !== s.alt) return false;
  return true;
}

// Skip shortcuts when the user is typing in a form field — except for
// shortcuts that explicitly require a modifier (those should still fire
// from inside an input).
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
  // Allow Cmd/Ctrl-modified shortcuts even in inputs.
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
