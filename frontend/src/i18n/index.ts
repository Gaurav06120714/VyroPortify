"use client";

/**
 * Lightweight i18n primitive (v2.2.0).
 *
 * Deliberately not pulling in next-intl yet — that's a bigger refactor
 * (locale-routed segments, middleware, RSC integration) and would
 * mean a full app re-routing pass. Instead we ship the strings, the
 * runtime hook, the LocaleSwitcher, and the persistence mechanism so
 * the codebase can start consuming `t()` calls today. When we adopt
 * next-intl we replace the implementation behind useTranslation()
 * without changing call sites.
 *
 * Storage: localStorage key `portify-locale`. Falls back to
 * navigator.language → en. SSR returns "en" deterministically so
 * hydration doesn't mismatch.
 */

import { useCallback, useEffect, useState } from "react";

import en from "./messages/en.json";
import es from "./messages/es.json";
import hi from "./messages/hi.json";

// Add new locales here. The whole catalog ships in the JS bundle for
// the v2.2.0 MVP — at next-intl adoption time we lazy-load each catalog.
const MESSAGES = { en, es, hi } as const;

export type Locale = keyof typeof MESSAGES;
export const SUPPORTED_LOCALES: Locale[] = ["en", "es", "hi"];

const STORAGE_KEY = "portify-locale";

function resolveInitial(): Locale {
  if (typeof window === "undefined") return "en";
  const saved = localStorage.getItem(STORAGE_KEY) as Locale | null;
  if (saved && SUPPORTED_LOCALES.includes(saved)) return saved;
  const browserLang = navigator.language?.split("-")[0] as Locale | undefined;
  return browserLang && SUPPORTED_LOCALES.includes(browserLang) ? browserLang : "en";
}

function getByPath(obj: Record<string, unknown>, path: string): string | undefined {
  // path like "hero.title" → drill into nested keys without dotting in TS.
  return path.split(".").reduce<unknown>(
    (acc, key) => (acc != null ? (acc as Record<string, unknown>)[key] : undefined),
    obj,
  ) as string | undefined;
}

interface UseTranslation {
  t: (key: string, fallback?: string) => string;
  locale: Locale;
  setLocale: (l: Locale) => void;
}

export function useTranslation(): UseTranslation {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    setLocaleState(resolveInitial());
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* ignore */
    }
    // Reflect on <html lang=…> for a11y + search engines.
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("lang", l);
    }
  }, []);

  const t = useCallback(
    (key: string, fallback?: string) => {
      const dict = MESSAGES[locale] as Record<string, unknown>;
      return (
        getByPath(dict, key) ??
        getByPath(MESSAGES.en as Record<string, unknown>, key) ??
        fallback ??
        key
      );
    },
    [locale],
  );

  return { t, locale, setLocale };
}
