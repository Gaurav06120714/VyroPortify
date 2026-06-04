"use client";

import { useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";
import * as Sentry from "@sentry/nextjs";

export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-[var(--pf-bg)] px-4 text-center">
      <p className="text-7xl font-extrabold text-[var(--pf-accent)] opacity-40">!</p>
      <h1 className="mt-4 text-2xl font-bold text-[var(--pf-text)]">
        Something went wrong
      </h1>
      <p className="mt-2 max-w-md text-[var(--pf-muted)]">
        We hit an unexpected error. The team has been notified — please try again.
      </p>
      {error.digest && (
        <p className="mt-2 text-xs text-[var(--pf-muted-darker)]">
          Reference: <code>{error.digest}</code>
        </p>
      )}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={reset}
          className="flex items-center gap-2 rounded-xl bg-[var(--pf-accent)] px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[var(--pf-accent-hover)]"
        >
          <RefreshCw className="h-4 w-4" />
          Try again
        </button>
        <Link
          href="/"
          className="flex items-center gap-2 rounded-xl border border-[var(--pf-border-light)] px-5 py-2.5 text-sm font-semibold text-[var(--pf-text)] transition-colors hover:bg-[var(--pf-surface)]"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>
      </div>
    </div>
  );
}
