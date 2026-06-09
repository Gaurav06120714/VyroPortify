"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useSearchParams, useRouter, useParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import {
  Eye,
  PenLine,
  ExternalLink,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api/v1";

type Tab = "edit" | "preview";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3007";

export default function BuilderPage() {
  const params = useParams<{ id: string }>();
  const search = useSearchParams();
  const router = useRouter();
  const portfolioId = params.id;

  const tabFromUrl = (search.get("tab") as Tab) === "preview" ? "preview" : "edit";
  const [tab, setTab] = useState<Tab>(tabFromUrl);

  useEffect(() => {
    setTab(tabFromUrl);
  }, [tabFromUrl]);

  function setTabAndUrl(next: Tab) {
    setTab(next);
    const sp = new URLSearchParams(search.toString());
    sp.set("tab", next);
    router.replace(`?${sp.toString()}`, { scroll: false });
  }

  const { getToken } = useAuth();
  const [previewSlug, setPreviewSlug] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  useEffect(() => {
    if (portfolioId === "new") {
      setPreviewSlug(null);
      return;
    }
    let alive = true;
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const res = await fetch(
          `${API_URL}/portfolio/${portfolioId}/status`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (!res.ok) {
          if (alive) setPreviewError("Portfolio not found");
          return;
        }
        const data = (await res.json()) as { slug?: string };
        if (alive && data.slug) setPreviewSlug(data.slug);
      } catch (e) {
        if (alive) setPreviewError(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => {
      alive = false;
    };
  }, [portfolioId, getToken]);

  const previewUrl = useMemo(
    () => (previewSlug ? `${SITE_URL}/portfolio/p/${previewSlug}` : null),
    [previewSlug],
  );

  return (
    <div className="flex h-[calc(100dvh-3.5rem)] flex-col">
      {}
      <header className="flex items-center justify-between border-b border-[var(--pf-border-light)] bg-[var(--pf-bg)] px-4 py-3 lg:px-6">
        <div className="flex items-center gap-3">
          <h1 className="text-h3 text-[var(--pf-text)]">Portfolio Builder</h1>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--pf-surface2)] px-2.5 py-1 text-xs text-[var(--pf-muted)]">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            Auto-saved
          </span>
        </div>

        {}
        <div className="flex items-center gap-2 lg:hidden" role="tablist" aria-label="Builder view">
          <TabButton active={tab === "edit"} onClick={() => setTabAndUrl("edit")}>
            <PenLine className="h-4 w-4" /> Edit
          </TabButton>
          <TabButton active={tab === "preview"} onClick={() => setTabAndUrl("preview")}>
            <Eye className="h-4 w-4" /> Preview
          </TabButton>
        </div>

        {previewUrl && (
          <Link
            href={previewUrl}
            target="_blank"
            rel="noopener"
            className="hidden items-center gap-1.5 text-sm text-[var(--pf-accent)] hover:underline lg:inline-flex"
          >
            Open public page <ExternalLink className="h-3.5 w-3.5" />
          </Link>
        )}
      </header>

      {}
      <div className="flex flex-1 overflow-hidden">
        {}
        <section
          role="tabpanel"
          aria-label="Edit"
          className={cn(
            "flex-1 overflow-y-auto border-r border-[var(--pf-border-light)] bg-[var(--pf-surface)]",
            "lg:max-w-[520px]",
            tab === "edit" ? "block" : "hidden lg:block",
          )}
        >
          <div className="p-6">
            <h2 className="text-h2 text-[var(--pf-text)]">Your information</h2>
            <p className="mt-1 text-sm text-[var(--pf-muted)]">
              The unified inline editor moves here in v1.7.4. For now, use the
              existing builder flow — your changes will appear in the preview
              pane on the right.
            </p>

            <div className="mt-6 space-y-3">
              <Link
                href="/dashboard/build-resume"
                className="block rounded-2xl border border-[var(--pf-border-light)] bg-[var(--pf-bg)] p-5 transition-colors hover:border-[var(--pf-accent)] hover:bg-[var(--pf-accent-subtle)]"
              >
                <div className="flex items-start gap-3">
                  <PenLine className="mt-0.5 h-5 w-5 text-[var(--pf-accent)]" />
                  <div>
                    <h3 className="font-semibold text-[var(--pf-text)]">
                      Open the 12-step builder
                    </h3>
                    <p className="mt-1 text-sm text-[var(--pf-muted)]">
                      Walk through personal details, experience, projects,
                      education, skills, and links.
                    </p>
                  </div>
                </div>
              </Link>

              <Link
                href="/dashboard/upload"
                className="block rounded-2xl border border-[var(--pf-border-light)] bg-[var(--pf-bg)] p-5 transition-colors hover:border-[var(--pf-accent)] hover:bg-[var(--pf-accent-subtle)]"
              >
                <div className="flex items-start gap-3">
                  <PenLine className="mt-0.5 h-5 w-5 text-[var(--pf-accent)]" />
                  <div>
                    <h3 className="font-semibold text-[var(--pf-text)]">
                      Upload a resume (PDF / DOCX)
                    </h3>
                    <p className="mt-1 text-sm text-[var(--pf-muted)]">
                      Let Claude extract everything automatically.
                    </p>
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </section>

        {}
        <section
          role="tabpanel"
          aria-label="Preview"
          className={cn(
            "relative flex-1 overflow-hidden bg-[var(--pf-surface2)]",
            tab === "preview" ? "block" : "hidden lg:block",
          )}
        >
          {previewUrl ? (
            <iframe
              key={previewUrl}
              src={previewUrl}
              title="Portfolio preview"
              className="h-full w-full border-0"
              
              sandbox="allow-scripts allow-same-origin"
              style={{ touchAction: "pinch-zoom" }}
            />
          ) : (
            <PreviewEmpty />
          )}
        </section>
      </div>

      {}
      <div className="border-t border-[var(--pf-border-light)] bg-[var(--pf-bg)] p-3 lg:hidden">
        {tab === "edit" ? (
          <button
            onClick={() => setTabAndUrl("preview")}
            className="flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--pf-accent)] text-sm font-semibold text-white transition-colors hover:bg-[var(--pf-accent-hover)]"
          >
            <Eye className="h-4 w-4" />
            See live preview
          </button>
        ) : (
          <button
            onClick={() => setTabAndUrl("edit")}
            className="flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] text-sm font-semibold text-[var(--pf-text)] transition-colors hover:bg-[var(--pf-surface2)]"
          >
            <PenLine className="h-4 w-4" />
            Back to edit
          </button>
        )}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
        active
          ? "bg-[var(--pf-accent)] text-white"
          : "text-[var(--pf-text-dim)] hover:bg-[var(--pf-surface2)]",
      )}
    >
      {children}
    </button>
  );
}

function PreviewEmpty() {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <div className="rounded-2xl border border-dashed border-[var(--pf-border-medium)] bg-[var(--pf-bg)] p-8">
        <Loader2 className="mx-auto h-8 w-8 animate-spin text-[var(--pf-accent)]" />
        <h3 className="mt-4 text-h3 text-[var(--pf-text)]">
          No preview yet
        </h3>
        <p className="mt-1 max-w-sm text-sm text-[var(--pf-muted)]">
          Fill in the form on the left and publish to see your portfolio live
          on this side of the page.
        </p>
        <div className="mt-5">
          <Link
            href="/dashboard/portfolios"
            className="inline-flex h-10 items-center justify-center rounded-xl bg-[var(--pf-accent)] px-4 text-sm font-semibold text-white transition-colors hover:bg-[var(--pf-accent-hover)]"
          >
            View portfolios →
          </Link>
        </div>
      </div>
    </div>
  );
}
