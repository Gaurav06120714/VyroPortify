"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

interface UseDebouncedSaveResult<T> {
  status: SaveStatus;
  lastSavedAt: Date | null;
  errorMessage: string | null;
  
  queue: (value: T) => void;
  
  flush: () => Promise<void>;
}

interface Options {
  
  debounceMs?: number;
}

export function useDebouncedSave<T>(
  save: (value: T) => Promise<void>,
  options: Options = {},
): UseDebouncedSaveResult<T> {
  const { debounceMs = 800 } = options;

  const [status, setStatus] = useState<SaveStatus>("idle");
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const pendingRef = useRef<{ value: T } | null>(null);
  
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

  const flushRef = useRef(flush);
  useEffect(() => {
    flushRef.current = flush;
  }, [flush]);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === "hidden") void flushRef.current();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  useEffect(() => () => void flushRef.current(), []);

  return { status, lastSavedAt, errorMessage, queue, flush };
}
