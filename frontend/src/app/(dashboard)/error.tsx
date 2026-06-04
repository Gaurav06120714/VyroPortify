"use client";

import { useEffect } from "react";
import { RefreshCw } from "lucide-react";
import * as Sentry from "@sentry/nextjs";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error, { tags: { surface: "dashboard" } });
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <h2 className="text-xl font-bold text-[var(--pf-text)]">
        This page hit a snag
      </h2>
      <p className="mt-2 max-w-md text-sm text-[var(--pf-muted)]">
        Your data is safe. Try reloading — if it keeps happening, the team has
        been notified.
      </p>
      {error.digest && (
        <p className="mt-2 text-xs text-[var(--pf-muted-darker)]">
          Reference: <code>{error.digest}</code>
        </p>
      )}
      <button
        onClick={reset}
        className="mt-6 flex items-center gap-2 rounded-xl bg-[var(--pf-accent)] px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[var(--pf-accent-hover)]"
      >
        <RefreshCw className="h-4 w-4" />
        Retry
      </button>
    </div>
  );
}
