"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import {
  ExternalLink, Trash2, Globe, Lock, RefreshCw, Upload, Loader2, Copy, Check,
} from "lucide-react";
import { getPortfolios, deletePortfolio, publishPortfolio } from "@/lib/api";
import type { Portfolio } from "@/types";

const STATUS_COLORS: Record<Portfolio["status"], string> = {
  queued: "var(--pf-muted)",
  generating: "#f59e0b",
  published: "#22c55e",
  failed: "#ef4444",
};

export default function PortfoliosPage() {
  const { getToken } = useAuth();
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchPortfolios = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const res = await getPortfolios(token);
      setPortfolios(res.items);
    } catch {
      toast.error("Failed to load portfolios.");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchPortfolios();
  }, [fetchPortfolios]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this portfolio? This cannot be undone.")) return;
    try {
      const token = await getToken();
      if (!token) return;
      await deletePortfolio(id, token);
      setPortfolios((prev) => prev.filter((p) => p.id !== id));
      toast.success("Portfolio deleted.");
    } catch {
      toast.error("Failed to delete portfolio.");
    }
  };

  const handleCopyLink = async (p: Portfolio) => {
    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
    const url = p.html_url ?? `${siteUrl}/portfolio/p/${p.slug}`;
    await navigator.clipboard.writeText(url);
    setCopiedId(p.id);
    toast.success("Link copied!");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleTogglePublish = async (portfolio: Portfolio) => {
    try {
      const token = await getToken();
      if (!token) return;
      const updated = await publishPortfolio(portfolio.id, token);
      setPortfolios((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      toast.success(updated.is_public ? "Portfolio published!" : "Portfolio unpublished.");
    } catch {
      toast.error("Failed to update portfolio.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--pf-text)]">My Portfolios</h1>
          <p className="mt-1 text-[var(--pf-muted)]">{portfolios.length} portfolio{portfolios.length !== 1 ? "s" : ""}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { setLoading(true); fetchPortfolios(); }}
            className="flex items-center gap-1.5 rounded-lg border border-[var(--pf-border-light)] px-3 py-2 text-sm text-[var(--pf-muted)] hover:text-[var(--pf-text)] transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <Link
            href="/dashboard/upload"
            className="flex items-center gap-1.5 rounded-lg bg-[var(--pf-accent)] px-3 py-2 text-sm font-semibold text-white hover:bg-[var(--pf-accent-hover)] transition-colors"
          >
            <Upload className="h-3.5 w-3.5" />
            New Portfolio
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-[var(--pf-accent)]" />
        </div>
      ) : portfolios.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-[var(--pf-border-light)] bg-[var(--pf-surface)] p-12 text-center">
          <p className="text-[var(--pf-muted)]">No portfolios yet. Upload a resume to get started.</p>
          <Link
            href="/dashboard/upload"
            className="flex items-center gap-2 rounded-lg bg-[var(--pf-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--pf-accent-hover)] transition-colors"
          >
            <Upload className="h-4 w-4" />
            Upload Resume
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {portfolios.map((p) => (
            <div
              key={p.id}
              className="flex items-center gap-4 rounded-xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-4"
            >
              {}
              <div
                className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
                style={{ background: STATUS_COLORS[p.status] }}
                title={p.status}
              />

              {}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="truncate font-medium text-[var(--pf-text)]">
                    {p.slug || p.id.slice(0, 8)}
                  </p>
                  <span className="rounded-full border border-[var(--pf-border-light)] px-2 py-0.5 text-xs capitalize text-[var(--pf-muted)]">
                    {p.template_id}
                  </span>
                  <span
                    className="rounded-full px-2 py-0.5 text-xs capitalize"
                    style={{
                      background: `${STATUS_COLORS[p.status]}22`,
                      color: STATUS_COLORS[p.status],
                    }}
                  >
                    {p.status}
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-[var(--pf-muted)]">
                  {p.views} views · {new Date(p.created_at).toLocaleDateString()}
                </p>
              </div>

              {}
              <div className="flex items-center gap-1">
                {p.status === "published" && (
                  <button
                    onClick={() => handleCopyLink(p)}
                    className="rounded-lg p-2 text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)] transition-colors"
                    title="Copy public link"
                  >
                    {copiedId === p.id ? (
                      <Check className="h-4 w-4 text-green-400" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </button>
                )}
                {p.status === "published" && p.html_url && (
                  <a
                    href={p.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-lg p-2 text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)] transition-colors"
                    title="View portfolio"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
                <button
                  onClick={() => handleTogglePublish(p)}
                  disabled={p.status !== "published"}
                  className="rounded-lg p-2 text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)] transition-colors disabled:opacity-40"
                  title={p.is_public ? "Make private" : "Make public"}
                >
                  {p.is_public ? (
                    <Globe className="h-4 w-4" />
                  ) : (
                    <Lock className="h-4 w-4" />
                  )}
                </button>
                <button
                  onClick={() => handleDelete(p.id)}
                  className="rounded-lg p-2 text-[var(--pf-muted)] hover:bg-[rgba(255,77,77,0.08)] hover:text-red-400 transition-colors"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
