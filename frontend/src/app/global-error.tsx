"use client";

import { useEffect } from "react";
import * as Sentry from "@sentry/nextjs";

export default function GlobalError({
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
    <html lang="en">
      <body
        style={{
          background: "#0a0a14",
          color: "#e6e6f0",
          fontFamily: "system-ui, -apple-system, sans-serif",
          minHeight: "100dvh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "2rem",
          textAlign: "center",
        }}
      >
        <div style={{ maxWidth: 420 }}>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.5rem" }}>
            Application error
          </h1>
          <p style={{ color: "#9999bb", marginBottom: "1.5rem" }}>
            VyroPortify ran into an unexpected problem. Please refresh the page.
          </p>
          {error.digest && (
            <p style={{ fontSize: "0.75rem", color: "#666688", marginBottom: "1.5rem" }}>
              Reference: <code>{error.digest}</code>
            </p>
          )}
          <button
            onClick={reset}
            style={{
              background: "#7c5cff",
              color: "#fff",
              padding: "0.65rem 1.25rem",
              borderRadius: "0.75rem",
              border: "none",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
