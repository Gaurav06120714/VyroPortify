"use client";

import { useEffect, useState } from "react";
import { Download, X } from "lucide-react";

// v2.2.1 — PWA registration + install prompt.
//
// Registers /sw.js once after first paint (idle callback so it never
// competes with hydration). When Chrome / Edge fire `beforeinstallprompt`,
// we capture it and show a low-key bottom-right banner the user can
// dismiss or accept. iOS Safari doesn't fire that event so this
// component is no-op there — install lives in the share menu instead.

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const DISMISS_KEY = "vyro-pwa-dismissed-at";
const DISMISS_TTL_MS = 1000 * 60 * 60 * 24 * 14; // 14 days

export function PwaInstallPrompt() {
  const [promptEvent, setPromptEvent] = useState<BeforeInstallPromptEvent | null>(
    null,
  );

  useEffect(() => {
    // Service worker — fire-and-forget, runs after first paint.
    if (
      "serviceWorker" in navigator &&
      process.env.NODE_ENV === "production"
    ) {
      const onLoad = () => {
        navigator.serviceWorker.register("/sw.js").catch(() => {
          // Registration failures are non-fatal — the app still works
          // without the SW, just no offline shell.
        });
      };
      if (document.readyState === "complete") onLoad();
      else window.addEventListener("load", onLoad, { once: true });
    }

    // Capture the install prompt so we can present it on our terms.
    const handler = (e: Event) => {
      // Suppress Chrome's default mini-bar; we'll show our own.
      e.preventDefault();
      // Honor a recent dismissal.
      const dismissed = Number(localStorage.getItem(DISMISS_KEY) || 0);
      if (Date.now() - dismissed < DISMISS_TTL_MS) return;
      setPromptEvent(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (!promptEvent) return null;

  async function install() {
    await promptEvent!.prompt();
    const choice = await promptEvent!.userChoice;
    if (choice.outcome === "dismissed") {
      localStorage.setItem(DISMISS_KEY, String(Date.now()));
    }
    setPromptEvent(null);
  }

  function dismiss() {
    localStorage.setItem(DISMISS_KEY, String(Date.now()));
    setPromptEvent(null);
  }

  return (
    <div
      role="dialog"
      aria-label="Install VyroPortify"
      className="fixed bottom-4 right-4 z-[var(--pf-z-toast)] max-w-sm rounded-2xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] p-4 shadow-[var(--pf-elev-3)]"
    >
      <button
        onClick={dismiss}
        aria-label="Dismiss install prompt"
        className="absolute right-2 top-2 rounded-md p-1 text-[var(--pf-muted)] hover:bg-[var(--pf-surface2)]"
      >
        <X className="h-4 w-4" />
      </button>
      <div className="flex items-start gap-3 pr-6">
        <div className="rounded-xl bg-[var(--pf-accent-subtle)] p-2 text-[var(--pf-accent)]">
          <Download className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-[var(--pf-text)]">
            Install VyroPortify
          </h3>
          <p className="mt-1 text-xs text-[var(--pf-muted)]">
            Get a one-tap shortcut on your home screen and offline access.
          </p>
          <div className="mt-3 flex gap-2">
            <button
              onClick={install}
              className="rounded-lg bg-[var(--pf-accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--pf-accent-hover)]"
            >
              Install
            </button>
            <button
              onClick={dismiss}
              className="rounded-lg px-3 py-1.5 text-xs font-medium text-[var(--pf-text-dim)] hover:bg-[var(--pf-surface2)]"
            >
              Not now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
