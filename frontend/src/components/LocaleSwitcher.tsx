"use client";

import { Globe } from "lucide-react";
import { useTranslation, SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { cn } from "@/lib/utils";

const LOCALE_LABELS: Record<Locale, string> = {
  en: "English",
  es: "Español",
  hi: "हिन्दी",
};

export function LocaleSwitcher({ className }: { className?: string }) {
  const { locale, setLocale } = useTranslation();

  return (
    <label className={cn("flex items-center gap-2 text-sm", className)}>
      <Globe className="h-4 w-4 text-[var(--pf-muted)]" aria-hidden />
      <span className="sr-only">Language</span>
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
        className="rounded-lg border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-2 py-1 text-[var(--pf-text)] focus:border-[var(--pf-accent)] focus:outline-none"
      >
        {SUPPORTED_LOCALES.map((l) => (
          <option key={l} value={l}>
            {LOCALE_LABELS[l]}
          </option>
        ))}
      </select>
    </label>
  );
}
