"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface Props {
  resumeId: string;
  templateId?: "modern" | "classic" | "compact";
  className?: string;
  label?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const POLL_INTERVAL_MS = 1200;
const POLL_TIMEOUT_MS = 60_000;

/**
 * v2.3.3 — One-tap resume PDF export.
 *
 * Flow:
 *   1. POST /resume/{id}/export-pdf → returns export_id.
 *      If `cached: true`, fetch the URL immediately and download.
 *      Otherwise enter the polling loop.
 *   2. Poll GET /resume/exports/{id} every 1.2s until status==completed
 *      (or 60s timeout). Show "Generating PDF…" toast while waiting.
 *   3. Open the returned presigned URL in a new tab so the browser
 *      handles the download natively (preserves Content-Disposition).
 */
export function DownloadPdfButton({
  resumeId,
  templateId = "modern",
  className,
  label = "Download PDF",
}: Props) {
  const { getToken } = useAuth();
  const [busy, setBusy] = useState(false);

  async function run() {
    if (busy) return;
    setBusy(true);
    const toastId = toast.loading("Generating PDF…");
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const startRes = await fetch(
        `${API_URL}/resume/${resumeId}/export-pdf?template_id=${templateId}`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` } },
      );
      if (!startRes.ok) {
        throw new Error((await startRes.text()) || "Export request failed");
      }
      const start = (await startRes.json()) as {
        export_id: string;
        status: string;
        cached?: boolean;
      };

      // Poll until ready or timeout.
      const exportId = start.export_id;
      const deadline = Date.now() + POLL_TIMEOUT_MS;
      let downloadUrl: string | null = null;
      while (Date.now() < deadline) {
        const statusRes = await fetch(
          `${API_URL}/resume/exports/${exportId}`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (statusRes.ok) {
          const data = (await statusRes.json()) as {
            status: string;
            download_url?: string;
          };
          if (data.status === "completed" && data.download_url) {
            downloadUrl = data.download_url;
            break;
          }
        }
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
      }

      if (!downloadUrl) {
        throw new Error("Timed out waiting for the PDF — please try again.");
      }

      // New tab so the browser handles Content-Disposition: attachment.
      window.open(downloadUrl, "_blank", "noopener,noreferrer");
      toast.success(start.cached ? "PDF ready (cached)" : "PDF ready", {
        id: toastId,
      });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err), {
        id: toastId,
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={run}
      disabled={busy}
      className={cn(
        "inline-flex items-center gap-2 rounded-xl bg-[var(--pf-accent)] px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-[var(--pf-accent-hover)] disabled:opacity-60",
        className,
      )}
    >
      {busy ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Download className="h-4 w-4" />
      )}
      {label}
    </button>
  );
}
