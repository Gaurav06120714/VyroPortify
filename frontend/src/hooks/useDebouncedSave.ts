"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

interface UseDebouncedSaveResult<T> {
  status: SaveStatus;
  lastSavedAt: Date | null;
  errorMessage: string | null;
  /** Call this on every field change. The hook batches and persists. */
  queue: (value: T) => void;
  /** Force-flush whatever is queued (e.g. on tab switch or unmount). */
  flush: () => Promise<void>;
}

interface Options {
  /** Quiet period before the save fires. Default 800 ms. */
  debounceMs?: number;
}

/**
 * Debounced auto-save with status reporting. Used by the unified builder
 * (v1.7.4) so every keystroke doesn't fire a request, and so the header
 * "Saved · 2s ago" pill has a single source of truth.
 *
 * The hook flushes the pending payload on tab hidden and on unmount so a
 * user who navigates away mid-typing doesn't lose their work.
 */
export function useDebouncedSave<T>(
  save: (value: T) => Promise<void>,
  options: Options = {},
): UseDebouncedSaveResult<T> {
  const { debounceMs = 800 } = options;

  const [status, setStatus] = useState<SaveStatus>("idle");
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Holds the most-recent queued value while we wait out the debounce.
  const pendingRef = useRef<{ value: T } | null>(null);
  // Active timeout so we can clear it on each new queue().
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const doSave = useCallback(async () => {
    if (!pendingRef.current) return;
    const value = pendingRef.current.value;
    pendingRef.current = null;
    setStatus("saving");
    setErrorMessage(null);
    try {
      await save(value);
      setStatus("saved");
      setLastSavedAt(new Date());
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  }, [save]);

  const queue = useCallback(
    (value: T) => {
      pendingRef.current = { value };
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(doSave, debounceMs);
    },
    [doSave, debounceMs],
  );

  const flush = useCallback(async () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    await doSave();
  }, [doSave]);

  // B23 fix: route flush through a ref so the "flush on unmount" and
  // "flush on tab hidden" effects don't re-fire every time `save`
  // changes identity. The previous version put `flush` in the
  // dependency list, which meant the cleanup ran on every render
  // that re-created doSave — silent duplicate saves.
  const flushRef = useRef(flush);
  useEffect(() => {
    flushRef.current = flush;
  }, [flush]);

  // Flush on tab hidden — if the user switches away mid-debounce we don't
  // want their last edits to disappear. Empty deps: mount-only.
  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === "hidden") void flushRef.current();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  // Flush on unmount — fires exactly once when the component unmounts.
  useEffect(() => () => void flushRef.current(), []);

  return { status, lastSavedAt, errorMessage, queue, flush };
}
