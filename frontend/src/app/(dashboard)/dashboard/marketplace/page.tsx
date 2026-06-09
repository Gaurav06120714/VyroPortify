"use client";

import { useEffect, useMemo, useState } from "react";
import { Search, Star, Tag } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { EmptyState } from "@/components/ui/EmptyState";

interface TemplateRow {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  preview_url: string | null;
  is_pro: boolean;
  price_cents: number;
  status: string;
  rating_average: number;
  rating_count: number;
  downloads_count: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api/v1";

export default function MarketplacePage() {
  const [rows, setRows] = useState<TemplateRow[] | null>(null);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch(
          `${API_URL}/marketplace/templates?limit=60&sort=popular`,
        );
        if (!res.ok) throw new Error("Failed to load templates");
        const data = (await res.json()) as TemplateRow[];
        if (alive) setRows(data);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!rows) return null;
    if (!q.trim()) return rows;
    const needle = q.toLowerCase();
    return rows.filter(
      (r) =>
        r.name.toLowerCase().includes(needle) ||
        (r.description ?? "").toLowerCase().includes(needle),
    );
  }, [rows, q]);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-h1 text-[var(--pf-text)]">Marketplace</h1>
        <p className="text-sm text-[var(--pf-muted)]">
          Browse community templates. Pro members can publish their own and
          earn revenue.
        </p>
      </header>

      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--pf-muted)]" />
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search templates…"
          className="pl-9"
          aria-label="Search templates"
        />
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {filtered === null && !error && (
        <div className="text-sm text-[var(--pf-muted)]">Loading…</div>
      )}

      {filtered?.length === 0 && !error && (
        <EmptyState
          icon={Tag}
          title="No templates yet"
          description={
            q
              ? "Try a different search term."
              : "Be the first to publish a template."
          }
        />
      )}

      {filtered && filtered.length > 0 && (
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((t) => (
            <li
              key={t.id}
              className="overflow-hidden rounded-2xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] shadow-[var(--pf-elev-1)] transition-shadow hover:shadow-[var(--pf-elev-2)]"
            >
              {t.preview_url ? (
                
                <img
                  src={t.preview_url}
                  alt={`${t.name} preview`}
                  className="aspect-video w-full object-cover"
                />
              ) : (
                <div className="aspect-video w-full bg-[var(--pf-surface2)]" />
              )}
              <div className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-[var(--pf-text)]">
                    {t.name}
                  </h3>
                  <PriceBadge cents={t.price_cents} />
                </div>
                {t.description && (
                  <p className="mt-1 line-clamp-2 text-sm text-[var(--pf-muted)]">
                    {t.description}
                  </p>
                )}
                <div className="mt-3 flex items-center gap-3 text-xs text-[var(--pf-muted)]">
                  {}
                  <Rating value={t.rating_average} count={t.rating_count} />
                  <span>·</span>
                  <span>{t.downloads_count.toLocaleString()} uses</span>
                  {t.category && (
                    <>
                      <span>·</span>
                      <span>{t.category}</span>
                    </>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PriceBadge({ cents }: { cents: number }) {
  if (cents <= 0) {
    return (
      <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600">
        Free
      </span>
    );
  }
  return (
    <span className="rounded-full bg-[var(--pf-accent-subtle)] px-2 py-0.5 text-xs font-medium text-[var(--pf-accent)]">
      ${(cents / 100).toFixed(2)}
    </span>
  );
}

function Rating({ value, count }: { value: number; count: number }) {
  if (count === 0) return <span>No ratings</span>;
  return (
    <span className="inline-flex items-center gap-1">
      <Star className="h-3 w-3 fill-current text-amber-500" />
      {value.toFixed(1)} <span className="text-[var(--pf-muted)]">({count})</span>
    </span>
  );
}
