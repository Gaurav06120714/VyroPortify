"use client";

import { use, useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  ExternalLink,
  Copy,
  Globe,
  Lock,
  ArrowLeft,
  RefreshCw,
  Loader2,
  Monitor,
  Smartphone,
} from "lucide-react";
import { getPortfolioStatus, publishPortfolio } from "@/lib/api";
import type { Portfolio } from "@/types";

interface Props {
  params: Promise<{ id: string }>;
}

type ViewMode = "desktop" | "mobile";

export default function PortfolioPreviewPage({ params }: Props) {
  const { id } = use(params);
  const { getToken } = useAuth();
  const router = useRouter();

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("desktop");

  const fetchPortfolio = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) return;
      
      const res = (await getPortfolioStatus(id, token)) as unknown as Portfolio;
      setPortfolio(res);
    } catch {
      toast.error("Failed to load portfolio.");
      router.push("/dashboard/portfolios");
    } finally {
      setLoading(false);
    }
  }, [id, getToken, router]);

  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  const publicUrl = portfolio?.slug
    ? `${typeof window !== "undefined" ? window.location.origin : ""}/portfolio/${portfolio.slug}`
    : null;

  const handleCopy = async () => {
    if (!publicUrl) return;
    await navigator.clipboard.writeText(publicUrl);
    setCopied(true);
    toast.success("Link copied!");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTogglePublish = async () => {
    if (!portfolio) return;
    setPublishing(true);
    try {
      const token = await getToken();
      if (!token) return;
      const updated = await publishPortfolio(id, token);
      setPortfolio(updated);
      toast.success(updated.is_public ? "Portfolio is now public!" : "Portfolio unpublished.");
    } catch {
      toast.error("Failed to update visibility.");
    } finally {
      setPublishing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--pf-accent)]" />
      </div>
    );
  }

  if (!portfolio) return null;

  return (
    <div className="flex h-full flex-col gap-0 -m-6">
      {}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex items-center gap-3 border-b border-[var(--pf-accent-soft)] bg-[var(--pf-bg)] px-4 py-3 flex-shrink-0"
      >
        {}
        <button
          onClick={() => router.push("/dashboard/portfolios")}
          className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-[var(--pf-muted)] hover:text-[var(--pf-text)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>

        <div className="h-4 w-px bg-[var(--pf-accent-soft)]" />

        {}
        <span className="flex-1 truncate text-sm font-medium text-[var(--pf-text)]">
          {portfolio.slug || id}
        </span>

        {}
        <div className="flex items-center rounded-lg border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-0.5">
          {(["desktop", "mobile"] as ViewMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setViewMode(m)}
              className={`flex h-7 w-8 items-center justify-center rounded-md transition-colors ${
                viewMode === m
                  ? "bg-[var(--pf-border-light)] text-[var(--pf-accent-text)]"
                  : "text-[var(--pf-muted)] hover:text-[var(--pf-text)]"
              }`}
            >
              {m === "desktop" ? (
                <Monitor className="h-3.5 w-3.5" />
              ) : (
                <Smartphone className="h-3.5 w-3.5" />
              )}
            </button>
          ))}
        </div>

        {}
        <button
          onClick={fetchPortfolio}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)] transition-colors"
          title="Refresh"
        >
          <RefreshCw className="h-4 w-4" />
        </button>

        {}
        <button
          onClick={handleCopy}
          disabled={!publicUrl}
          className="flex items-center gap-1.5 rounded-lg border border-[var(--pf-border-light)] px-3 py-1.5 text-sm text-[var(--pf-muted)] hover:border-[rgba(108,99,255,0.5)] hover:text-[var(--pf-text)] transition-colors disabled:opacity-40"
        >
          <Copy className="h-3.5 w-3.5" />
          {copied ? "Copied!" : "Copy link"}
        </button>

        {}
        {portfolio.html_url && (
          <a
            href={portfolio.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-[var(--pf-border-light)] px-3 py-1.5 text-sm text-[var(--pf-muted)] hover:border-[rgba(108,99,255,0.5)] hover:text-[var(--pf-text)] transition-colors"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Open
          </a>
        )}

        {}
        <button
          onClick={handleTogglePublish}
          disabled={publishing || portfolio.status !== "published"}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors disabled:opacity-50 ${
            portfolio.is_public
              ? "bg-[rgba(34,197,94,0.12)] text-green-400 hover:bg-[rgba(34,197,94,0.2)]"
              : "bg-[var(--pf-accent)] text-white hover:bg-[var(--pf-accent-hover)]"
          }`}
        >
          {publishing ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : portfolio.is_public ? (
            <Globe className="h-3.5 w-3.5" />
          ) : (
            <Lock className="h-3.5 w-3.5" />
          )}
          {portfolio.is_public ? "Published" : "Publish"}
        </button>
      </motion.div>

      {}
      <div className="flex flex-1 items-start justify-center overflow-auto bg-[#080810] p-4">
        {portfolio.html_url ? (
          <motion.div
            key={viewMode}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className={`relative overflow-hidden rounded-xl border border-[var(--pf-accent-soft)] shadow-2xl transition-all ${
              viewMode === "mobile" ? "w-[390px]" : "w-full max-w-6xl"
            }`}
            style={{ height: viewMode === "mobile" ? "844px" : "calc(100vh - 140px)" }}
          >
            <iframe
              src={portfolio.html_url}
              className="h-full w-full border-0"
              title="Portfolio preview"
              sandbox="allow-scripts allow-same-origin"
            />
          </motion.div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-center">
            <Loader2 className="h-6 w-6 animate-spin text-[var(--pf-accent)]" />
            <p className="text-sm text-[var(--pf-muted)]">
              {portfolio.status === "generating"
                ? "Portfolio is still generating…"
                : "No preview available yet."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
