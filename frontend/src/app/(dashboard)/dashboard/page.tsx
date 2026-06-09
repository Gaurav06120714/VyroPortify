"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useUser, useAuth } from "@clerk/nextjs";
import { motion } from "framer-motion";
import {
  Upload,
  Palette,
  ArrowRight,
  FolderOpen,
  Eye,
  Zap,
  PenLine,
  Sparkles,
  FileText,
} from "lucide-react";
import { getPortfolios } from "@/lib/api";
import { usePlan } from "@/context/PlanContext";

const QUICK_ACTIONS = [
  {
    href: "/dashboard/build-resume",
    icon: PenLine,
    label: "AI Resume Builder",
    description: "Answer 12 questions — Claude writes your resume",
    accent: "var(--pf-accent)",
    badge: "✨ New",
  },
  {
    href: "/dashboard/upload",
    icon: Upload,
    label: "Upload Resume",
    description: "Upload a PDF or DOCX to get started",
    accent: "#00d4ff",
    badge: null,
  },
  {
    href: "/dashboard/cover-letter",
    icon: FileText,
    label: "Cover Letter",
    description: "Generate a tailored cover letter with AI",
    accent: "#ff6b9d",
    badge: "✨ New",
  },
  {
    href: "/dashboard/templates",
    icon: Palette,
    label: "Browse Templates",
    description: "Explore Aurora, Minimal, Cyber & Executive",
    accent: "#f59e0b",
    badge: null,
  },
];

export default function DashboardPage() {
  const { user } = useUser();
  const { getToken } = useAuth();
  const { plan } = usePlan();
  const name = user?.firstName ?? user?.username ?? "there";
  const [portfolioCount, setPortfolioCount] = useState<number | null>(null);
  const [totalViews, setTotalViews] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const res = await getPortfolios(token, 1, 100);
        setPortfolioCount(res.total);
        setTotalViews(res.items.reduce((sum, p) => sum + (p.views ?? 0), 0));
      } catch {
        
      }
    })();
  }, [getToken]);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-2xl font-bold text-[var(--pf-text)]">Hey, {name} 👋</h1>
        <p className="mt-1 text-[var(--pf-muted)]">
          Here&apos;s what&apos;s happening with your portfolios.
        </p>
      </motion.div>

      {}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05, duration: 0.3 }}
      >
        <Link
          href="/dashboard/build-resume"
          className="group relative flex items-center justify-between overflow-hidden rounded-2xl border border-[var(--pf-border-hover)] bg-gradient-to-r from-[var(--pf-surface)] to-[#0f0f1a] p-6 transition-all hover:border-[var(--pf-border-hover)] hover:shadow-[0_0_40px_var(--pf-accent-subtle)]"
        >
          {}
          <div className="pointer-events-none absolute right-0 top-0 h-48 w-48 rounded-full bg-[var(--pf-accent)] opacity-5 blur-3xl" />

          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--pf-accent-soft)]">
              <Sparkles className="h-6 w-6 text-[var(--pf-accent)]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="text-lg font-bold text-[var(--pf-text)]">AI Resume Builder</p>
                <span className="rounded-full bg-[var(--pf-border-light)] px-2 py-0.5 text-xs font-semibold text-[var(--pf-accent-text)]">
                  NEW
                </span>
              </div>
              <p className="text-sm text-[var(--pf-muted)]">
                No resume? No problem. Answer 12 quick questions and Claude builds it for you.
              </p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 flex-shrink-0 text-[var(--pf-muted)] transition-transform group-hover:translate-x-1 group-hover:text-[var(--pf-accent)]" />
        </Link>
      </motion.div>

      {}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.3 }}
        className="grid grid-cols-1 gap-4 sm:grid-cols-3"
      >
        <StatCard icon={<FolderOpen className="h-5 w-5" />} label="Portfolios" value={portfolioCount === null ? "—" : String(portfolioCount)} accent="var(--pf-accent)" />
        <StatCard icon={<Eye className="h-5 w-5" />} label="Total Views" value={totalViews === null ? "—" : String(totalViews)} accent="#00d4ff" />
        <StatCard icon={<Zap className="h-5 w-5" />} label="Plan" value={plan === "pro" ? "Pro" : "Free"} accent="#ff6b9d" />
      </motion.div>

      {}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.3 }}
      >
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--pf-muted)]">
          Get Started
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {QUICK_ACTIONS.map(({ href, icon: Icon, label, description, accent, badge }) => (
            <Link
              key={href}
              href={href}
              className="group flex flex-col gap-3 rounded-xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-5 transition-all hover:border-[var(--pf-border-hover)] hover:bg-[var(--pf-surface2)]"
            >
              <div className="flex items-center justify-between">
                <div
                  className="flex h-10 w-10 items-center justify-center rounded-lg"
                  style={{ background: `${accent}22` }}
                >
                  <Icon className="h-5 w-5" style={{ color: accent }} />
                </div>
                {badge && (
                  <span className="rounded-full bg-[var(--pf-accent-soft)] px-2 py-0.5 text-xs font-medium text-[var(--pf-accent-text)]">
                    {badge}
                  </span>
                )}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-[var(--pf-text)]">{label}</p>
                <p className="mt-0.5 text-sm text-[var(--pf-muted)]">{description}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-[var(--pf-muted)] transition-transform group-hover:translate-x-1 group-hover:text-[var(--pf-text)]" />
            </Link>
          ))}
        </div>
      </motion.div>

      {}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.3 }}
        className="rounded-xl border border-[var(--pf-border-dim)] bg-[var(--pf-surface)] p-5"
      >
        <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-[var(--pf-muted)]">
          How VyroPortify works
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[
            { step: "1", label: "Add your info", desc: "Build or upload your resume" },
            { step: "2", label: "Pick a theme", desc: "Aurora, Minimal, or Cyber" },
            { step: "3", label: "Go live", desc: "Share your portfolio URL instantly" },
          ].map(({ step, label, desc }) => (
            <div key={step} className="flex items-start gap-3">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-[var(--pf-accent-soft)] text-xs font-bold text-[var(--pf-accent)]">
                {step}
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--pf-text)]">{label}</p>
                <p className="text-xs text-[var(--pf-muted)]">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--pf-muted)]">{label}</p>
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg"
          style={{ background: `${accent}22`, color: accent }}
        >
          {icon}
        </div>
      </div>
      <p className="mt-3 text-3xl font-bold text-[var(--pf-text)]">{value}</p>
    </div>
  );
}
