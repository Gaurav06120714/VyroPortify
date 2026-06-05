"use client";

import Link from "next/link";
import { ArrowRight, Play, Sparkles } from "lucide-react";

export default function HeroSection() {
  return (
    <section className="flex min-h-dvh flex-col items-center justify-center px-6 pt-20 pb-24">
      <div className="mx-auto max-w-5xl text-center">
        {/* Badge — token-driven so it picks up Clarity blue or Aurora
            violet depending on the active palette. */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--pf-border-light)] bg-[var(--pf-accent-subtle)] px-4 py-1.5 text-sm font-medium text-[var(--pf-accent-text)]">
          <Sparkles className="h-3.5 w-3.5" />
          Built with Claude AI · Free to start
        </div>

        {/* Headline — uses v1.7.1 .text-display utilities for consistent
            tracking and weight across the marketing surface. */}
        <h1 className="text-display sm:text-display-lg text-[var(--pf-text)]">
          Turn your resume into{" "}
          <br />
          {/* UX-01: removed the violet underline below the hero phrase —
              read as a heavy form-input cursor on the white surface and
              fought with the headline's tight tracking. */}
          <span className="inline-block">a portfolio that gets you hired</span>
        </h1>

        {/* Sub */}
        <p className="mx-auto mt-7 max-w-2xl text-lg leading-relaxed text-[var(--pf-muted)] sm:text-xl">
          Upload your resume or answer 12 quick questions. Claude reads your experience, writes the copy, and builds your portfolio. The whole thing takes about 60 seconds.
        </p>

        {/* CTAs */}
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          {/* Primary CTA — Clarity uses warm amber (Gridlock pattern), Aurora
              keeps the violet via the same accent var. We pick warm here
              specifically because the hero is the single highest-intent CTA. */}
          <Link
            href="/register"
            className="group flex items-center gap-2 rounded-2xl bg-[var(--pf-cta-warm,var(--pf-accent))] px-7 py-3.5 text-base font-semibold text-white shadow-[var(--pf-elev-2)] transition-all hover:bg-[var(--pf-cta-warm-hover,var(--pf-accent-hover))]"
          >
            Generate your portfolio free
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>

          <Link
            href="#how-it-works"
            className="flex items-center gap-2 rounded-2xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-7 py-3.5 text-base font-semibold text-[var(--pf-text)] transition-all hover:border-[var(--pf-accent)] hover:bg-[var(--pf-surface2)]"
          >
            <Play className="h-4 w-4 fill-current" />
            See how it works
          </Link>
        </div>

        <p className="mt-4 text-sm text-muted-foreground/80">
          Free to start · No credit card · 60-second portfolio
        </p>
      </div>
    </section>
  );
}
