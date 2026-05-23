"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuth } from "@clerk/nextjs";
import {
  Eye,
  MousePointerClick,
  TrendingUp,
  Globe,
  Calendar,
  ArrowUpRight,
  ChevronRight,
  Users,
} from "lucide-react";
import { getPortfolios } from "@/lib/api";

interface Portfolio {
  id: string;
  slug?: string;
  title?: string;
  is_published?: boolean;
}

interface PortfolioStat {
  id: string;
  title: string;
  slug: string;
  views: number;
  clicks: number;
  ctr: number;
  topReferrer: string;
}

// Realistic mock data — replace with real analytics endpoint
function generateMockStats(portfolios: Portfolio[]): PortfolioStat[] {
  const referrers = ["LinkedIn", "Twitter", "Direct", "Google", "GitHub"];
  return portfolios.map((p, i) => {
    const views = 120 + Math.floor(Math.random() * 400) + i * 50;
    const clicks = Math.floor(views * (0.08 + Math.random() * 0.18));
    return {
      id: p.id,
      title: p.title || "Untitled portfolio",
      slug: p.slug || `portfolio-${i}`,
      views,
      clicks,
      ctr: clicks / views,
      topReferrer: referrers[i % referrers.length],
    };
  });
}

function generateWeeklyTrend(): number[] {
  return Array.from({ length: 7 }, () => 30 + Math.floor(Math.random() * 90));
}

export default function AnalyticsPage() {
  const { getToken } = useAuth();
  const [, setPortfolios] = useState<Portfolio[]>([]);
  const [stats, setStats] = useState<PortfolioStat[]>([]);
  const [weeklyTrend] = useState(generateWeeklyTrend());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const token = (await getToken()) || "";
        const res = await getPortfolios(token);
        const list = (res?.items || []) as Portfolio[];
        setPortfolios(list);
        setStats(generateMockStats(list.slice(0, 5)));
      } catch {
        // graceful — keep empty state
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [getToken]);

  const totalViews = stats.reduce((a, s) => a + s.views, 0);
  const totalClicks = stats.reduce((a, s) => a + s.clicks, 0);
  const avgCtr = stats.length > 0 ? (totalClicks / totalViews) * 100 : 0;
  const trendMax = Math.max(...weeklyTrend, 1);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[28px] font-bold tracking-tight text-[var(--pf-text)]">
            Analytics
          </h1>
          <p className="mt-0.5 text-[13px] text-[var(--pf-muted)]">
            Track views, clicks, and traffic across your portfolios
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-[var(--pf-border-subtle)] bg-[var(--pf-surface)] px-3 py-1.5 text-[12px] text-[var(--pf-muted)]">
          <Calendar className="h-3.5 w-3.5" />
          Last 30 days
        </div>
      </div>

      {/* Top stat cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard
          icon={<Eye className="h-4 w-4" />}
          label="Total views"
          value={totalViews.toLocaleString()}
          delta="+18%"
          deltaColor="text-emerald-500"
        />
        <StatCard
          icon={<MousePointerClick className="h-4 w-4" />}
          label="Total clicks"
          value={totalClicks.toLocaleString()}
          delta="+12%"
          deltaColor="text-emerald-500"
        />
        <StatCard
          icon={<TrendingUp className="h-4 w-4" />}
          label="Avg. CTR"
          value={`${avgCtr.toFixed(1)}%`}
          delta="+2.4pp"
          deltaColor="text-emerald-500"
        />
      </div>

      {/* Trend chart */}
      <div className="card-calm p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-[15px] font-semibold text-[var(--pf-text)]">
              Views this week
            </h2>
            <p className="text-[12px] text-[var(--pf-muted)]">
              Daily traffic across all your published portfolios
            </p>
          </div>
          <Users className="h-4 w-4 text-[var(--pf-accent-text)]" />
        </div>
        <div className="flex h-32 items-end justify-between gap-2">
          {weeklyTrend.map((v, i) => {
            const heightPct = (v / trendMax) * 100;
            const day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i];
            return (
              <div
                key={day}
                className="group flex flex-1 flex-col items-center gap-1.5"
              >
                <div className="relative flex h-full w-full items-end">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${heightPct}%` }}
                    transition={{
                      duration: 0.6,
                      delay: i * 0.05,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                    className="w-full rounded-md bg-[var(--pf-accent)] opacity-80 transition-opacity group-hover:opacity-100"
                  />
                  <div className="absolute -top-7 left-1/2 -translate-x-1/2 rounded bg-[var(--pf-text)] px-1.5 py-0.5 text-[10px] font-mono text-white opacity-0 transition-opacity group-hover:opacity-100">
                    {v}
                  </div>
                </div>
                <span className="text-[10px] text-[var(--pf-muted)]">{day}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Per-portfolio breakdown */}
      <div className="card-calm overflow-hidden">
        <div className="border-b border-[var(--pf-border-subtle)] px-5 py-3.5">
          <h2 className="text-[15px] font-semibold text-[var(--pf-text)]">
            Per-portfolio breakdown
          </h2>
          <p className="text-[12px] text-[var(--pf-muted)]">
            Top performers ranked by views
          </p>
        </div>

        {loading ? (
          <div className="space-y-2 p-5">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-14 animate-pulse rounded-lg bg-[var(--pf-border-subtle)]"
              />
            ))}
          </div>
        ) : stats.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="divide-y divide-[var(--pf-border-subtle)]">
            {[...stats]
              .sort((a, b) => b.views - a.views)
              .map((s, i) => (
                <motion.div
                  key={s.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: i * 0.04 }}
                  className="flex items-center justify-between gap-4 px-5 py-3.5 transition-colors hover:bg-[var(--pf-border-subtle)]"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[var(--pf-accent-subtle)] text-[11px] font-bold text-[var(--pf-accent-text)]">
                      #{i + 1}
                    </div>
                    <div className="min-w-0">
                      <div className="truncate text-[14px] font-semibold text-[var(--pf-text)]">
                        {s.title}
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-[var(--pf-muted)]">
                        <Globe className="h-2.5 w-2.5" />
                        /{s.slug}
                      </div>
                    </div>
                  </div>

                  <div className="hidden items-center gap-5 text-right md:flex">
                    <Metric label="Views" value={s.views.toLocaleString()} />
                    <Metric label="Clicks" value={s.clicks.toLocaleString()} />
                    <Metric label="CTR" value={`${(s.ctr * 100).toFixed(1)}%`} />
                    <Metric label="Top source" value={s.topReferrer} muted />
                  </div>

                  <Link
                    href={`/portfolio/${s.slug}`}
                    target="_blank"
                    className="flex shrink-0 items-center gap-1 rounded-md border border-[var(--pf-border-subtle)] px-2.5 py-1.5 text-[11px] font-medium text-[var(--pf-muted)] transition-colors hover:border-[var(--pf-border-medium)] hover:text-[var(--pf-text)]"
                  >
                    Open <ArrowUpRight className="h-3 w-3" />
                  </Link>
                </motion.div>
              ))}
          </div>
        )}
      </div>

      {/* Insights card */}
      <div className="card-calm border-[var(--pf-border-medium)] p-5">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--pf-accent-subtle)]">
            <TrendingUp className="h-4 w-4 text-[var(--pf-accent-text)]" />
          </div>
          <div className="flex-1">
            <h3 className="text-[14px] font-semibold text-[var(--pf-text)]">
              Insight
            </h3>
            <p className="mt-1 text-[13px] leading-relaxed text-[var(--pf-muted)]">
              Your top portfolio gets <strong className="text-[var(--pf-text)]">3.2x</strong> more
              views from LinkedIn than other sources. Consider adding a richer
              OG image and tightening your tagline to lift CTR further.
            </p>
            <Link
              href="/dashboard/portfolios"
              className="mt-3 inline-flex items-center gap-1 text-[12px] font-medium text-[var(--pf-accent-text)] hover:underline"
            >
              Open portfolios <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  delta,
  deltaColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  delta: string;
  deltaColor: string;
}) {
  return (
    <div className="card-calm p-5">
      <div className="flex items-center justify-between">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--pf-accent-subtle)] text-[var(--pf-accent-text)]">
          {icon}
        </div>
        <span className={`text-[11px] font-semibold ${deltaColor}`}>{delta}</span>
      </div>
      <div className="mt-4">
        <div className="text-[24px] font-bold tracking-tight text-[var(--pf-text)]">
          {value}
        </div>
        <div className="text-[12px] text-[var(--pf-muted)]">{label}</div>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  muted = false,
}: {
  label: string;
  value: string;
  muted?: boolean;
}) {
  return (
    <div className="text-right">
      <div className="text-[10px] uppercase tracking-[0.08em] text-[var(--pf-muted-dim)]">
        {label}
      </div>
      <div
        className={`text-[13px] font-semibold ${
          muted ? "text-[var(--pf-muted)]" : "text-[var(--pf-text)]"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="py-12 text-center">
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-[var(--pf-accent-subtle)]">
        <Eye className="h-4 w-4 text-[var(--pf-accent-text)]" />
      </div>
      <h3 className="text-[15px] font-semibold text-[var(--pf-text)]">
        No portfolios yet
      </h3>
      <p className="mt-1 text-[13px] text-[var(--pf-muted)]">
        Publish a portfolio to start seeing analytics here.
      </p>
      <Link
        href="/dashboard/build-resume"
        className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-[var(--pf-accent)] px-4 py-2 text-[13px] font-semibold text-white transition-colors hover:bg-[var(--pf-accent-hover)]"
      >
        Create portfolio <ArrowUpRight className="h-3 w-3" />
      </Link>
    </div>
  );
}
