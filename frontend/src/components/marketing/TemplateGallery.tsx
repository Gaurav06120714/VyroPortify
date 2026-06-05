"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Eye } from "lucide-react";
import FadeUp from "./FadeUp";

const TEMPLATES = [
  {
    id: "aurora",
    name: "Aurora",
    tag: "Most popular",
    tagColor: "var(--pf-accent)",
    desc: "Dark theme with a bold layout. Works well if you want your portfolio to stand out rather than blend in.",
    bg: "#0F0F1A",
    accent: "var(--pf-accent)",
    secondary: "#00d4ff",
    hero: "from-[var(--pf-accent)]/20 to-[#00d4ff]/10",
    skills: ["React", "TypeScript", "Node.js"],
  },
  {
    id: "minimal",
    name: "Minimal",
    tag: "Clean & classic",
    tagColor: "#00c896",
    desc: "Clean, light, and easy to read. Works for pretty much any role or industry.",
    bg: "#FAFAFA",
    accent: "#1a1a1a",
    secondary: "#4f46e5",
    hero: "from-slate-100 to-white",
    skills: ["Product", "Strategy", "Research"],
  },
  {
    id: "cyber",
    name: "Cyber",
    tag: "Stand out",
    tagColor: "#00FF88",
    desc: "High contrast with a terminal feel. Good for engineers, security folks, or anyone who wants something a bit different.",
    bg: "#0A0A0F",
    accent: "#00FF88",
    secondary: "#FF00AA",
    hero: "from-[#00FF88]/10 to-[#FF00AA]/10",
    skills: ["Solidity", "Rust", "Go"],
  },
];

function TemplateCard({ tpl, index }: { tpl: (typeof TEMPLATES)[0]; index: number }) {
  const [hovered, setHovered] = useState(false);
  const isDark = tpl.id !== "minimal";

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="group relative overflow-hidden rounded-2xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] transition-all duration-300 hover:border-[var(--pf-border-hover)]"
    >
      {/* Preview area */}
      <div
        className="relative h-56 w-full overflow-hidden"
        style={{ background: tpl.bg }}
      >
        {/* Faux browser bar */}
        <div
          className="flex h-8 items-center gap-1.5 px-3"
          style={{ background: isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.05)" }}
        >
          <div className="h-2 w-2 rounded-full bg-red-400/60" />
          <div className="h-2 w-2 rounded-full bg-yellow-400/60" />
          <div className="h-2 w-2 rounded-full bg-green-400/60" />
        </div>

        {/* Simulated content */}
        <div className={`absolute inset-0 top-8 flex flex-col gap-3 bg-gradient-to-br ${tpl.hero} p-5`}>
          {/* Hero strip */}
          <div className="flex items-center gap-3">
            <div
              className="h-10 w-10 flex-shrink-0 rounded-full"
              style={{ background: `linear-gradient(135deg, ${tpl.accent}, ${tpl.secondary})` }}
            />
            <div className="space-y-1.5">
              <div
                className="h-3 w-28 rounded-full"
                style={{ background: tpl.accent, opacity: 0.7 }}
              />
              <div
                className="h-2 w-18 rounded-full"
                style={{ background: tpl.secondary, opacity: 0.4 }}
              />
            </div>
          </div>
          {/* Skill chips */}
          <div className="flex gap-2">
            {tpl.skills.map((s) => (
              <div
                key={s}
                className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold"
                style={{
                  background: `${tpl.accent}20`,
                  color: tpl.accent,
                  border: `1px solid ${tpl.accent}40`,
                }}
              >
                {s}
              </div>
            ))}
          </div>
          {/* Project cards */}
          <div className="mt-1 grid grid-cols-2 gap-2">
            {[...Array(2)].map((_, i) => (
              <div
                key={i}
                className="h-12 rounded-xl p-2.5"
                style={{
                  background: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.04)",
                  border: `1px solid ${tpl.accent}20`,
                }}
              >
                <div
                  className="mb-1 h-1.5 w-3/4 rounded-full"
                  style={{ background: tpl.accent, opacity: 0.5 }}
                />
                <div
                  className="h-1 w-1/2 rounded-full"
                  style={{ background: tpl.secondary, opacity: 0.3 }}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Hover overlay */}
        {hovered && (
          <div className="absolute inset-0 flex items-center justify-center gap-3 bg-black/50">
            <Link
              href={`/register?template=${tpl.id}`}
              className="flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold text-white"
              style={{ background: tpl.accent }}
            >
              Use template <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <button className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-white/10 text-white">
              <Eye className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-5">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-white">{tpl.name}</h3>
          <span
            className="rounded-full px-2.5 py-0.5 text-xs font-semibold"
            style={{ background: `${tpl.tagColor}18`, color: tpl.tagColor }}
          >
            {tpl.tag}
          </span>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-[var(--pf-muted)]">{tpl.desc}</p>
      </div>
    </div>
  );
}

export default function TemplateGallery() {
  return (
    <section id="templates" className="relative px-6 py-28">
      <div className="pointer-events-none absolute right-0 top-1/2 h-96 w-96 -translate-y-1/2 rounded-full bg-[#00d4ff] opacity-5 blur-3xl" />
      <div className="mx-auto max-w-6xl">
        <FadeUp className="mb-16 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[var(--pf-border-hover)] bg-[var(--pf-border-subtle)] px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-[var(--pf-accent)]">
            Templates
          </div>
          {/* UX-02: was text-white — invisible on the light surface that
              shipped in v1.7.2. Switched to the --pf-text token so it
              follows the active palette. */}
          <h2 className="text-h1 sm:text-display text-[var(--pf-text)]">
            Three themes
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[var(--pf-muted)]">
            All three are fully responsive, SEO-ready, and mobile-friendly. Switch between them any time without re-entering your information.
          </p>
        </FadeUp>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {TEMPLATES.map((tpl, i) => (
            <TemplateCard key={tpl.id} tpl={tpl} index={i} />
          ))}
        </div>

        <FadeUp delay={0.3} className="mt-10 text-center">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-xl border border-[var(--pf-border-medium)] px-6 py-3 text-sm font-semibold text-[var(--pf-text-dim)] transition-all hover:border-[var(--pf-border-hover)] hover:bg-[var(--pf-border-subtle)]"
          >
            Browse all templates <ArrowRight className="h-4 w-4" />
          </Link>
        </FadeUp>
      </div>
    </section>
  );
}
