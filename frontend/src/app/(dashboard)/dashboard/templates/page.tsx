"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Check, ArrowRight, Monitor, Smartphone, X } from "lucide-react";

const TEMPLATES = [
  {
    id: "aurora" as const,
    name: "Aurora",
    tagline: "Dark electric — bold first impressions",
    description:
      "A dark, electric portfolio with animated gradient hero, glowing project cards, and Space Grotesk typography. Built for developers and designers who want to command attention.",
    bg: "#0F0F1A",
    accent: "var(--pf-accent)",
    secondary: "#00d4ff",
    tags: ["Dark", "Animated", "Developer"],
    features: [
      "Gradient animated hero",
      "Glowing skill chips",
      "Timeline experience section",
      "Project cards with hover glow",
      "Contact grid with icons",
    ],
    preview: {
      nav: "#1a1a2e",
      hero: "linear-gradient(135deg, var(--pf-accent)22, #00d4ff11)",
      card: "var(--pf-surface)",
    },
  },
  {
    id: "minimal" as const,
    name: "Minimal",
    tagline: "Clean white — timeless professionalism",
    description:
      "A clean, white portfolio built around typography and whitespace. Sticky navigation, DM Sans font, and a focus on content over effects. Loved by product managers and researchers.",
    bg: "#FAFAFA",
    accent: "#1a1a1a",
    secondary: "#4f46e5",
    tags: ["Light", "Clean", "Professional"],
    features: [
      "Sticky navigation bar",
      "Typography-first layout",
      "Clean skill tags",
      "Minimal project grid",
      "Simple contact section",
    ],
    preview: {
      nav: "#ffffff",
      hero: "linear-gradient(135deg, #f5f5ff, #fafafa)",
      card: "#ffffff",
    },
  },
  {
    id: "cyber" as const,
    name: "Cyber",
    tagline: "Neon glassmorphism — stand out completely",
    description:
      "Neon glassmorphism meets terminal aesthetics. Dark cyberpunk palette with scanline overlays, glowing accents, and terminal-style section labels. For those who refuse to blend in.",
    bg: "#0A0A0F",
    accent: "#00FF88",
    secondary: "#FF00AA",
    tags: ["Neon", "Glassmorphism", "Cyberpunk"],
    features: [
      "Neon glow effects",
      "Glassmorphism cards",
      "Terminal-style labels",
      "CSS scanline overlay",
      "Multi-color neon palette",
    ],
    preview: {
      nav: "rgba(0,255,136,0.05)",
      hero: "linear-gradient(135deg, #00FF8811, #FF00AA08)",
      card: "rgba(255,255,255,0.04)",
    },
  },
  {
    id: "executive" as const,
    name: "Executive",
    tagline: "Two-column serif — refined leadership presence",
    description:
      "A sophisticated two-column layout with a dark sidebar and light main content area. Playfair Display serif headings, gold accents, and editorial spacing. Perfect for senior engineers, managers, and executives.",
    bg: "#FAFAF8",
    accent: "#D4A853",
    secondary: "#111827",
    tags: ["Light", "Serif", "Executive"],
    features: [
      "Two-column sidebar layout",
      "Playfair Display serif headings",
      "Gold accent palette",
      "Numbered section markers",
      "Skills in sidebar",
    ],
    preview: {
      nav: "#111827",
      hero: "linear-gradient(135deg, #D4A85311, #FAFAF8)",
      card: "#ffffff",
    },
  },
];

type ViewMode = "desktop" | "mobile";

export default function TemplatesPage() {
  const router = useRouter();
  const [selected, setSelected] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("desktop");
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const handleUse = (id: string) => {
    router.push(`/dashboard/upload?template=${id}`);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--pf-text)]">Templates</h1>
          <p className="mt-1 text-[var(--pf-muted)]">
            Choose the perfect style for your portfolio — all are responsive and SEO-ready.
          </p>
        </div>
        {}
        <div className="flex items-center rounded-lg border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-0.5">
          {(["desktop", "mobile"] as ViewMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setViewMode(m)}
              className={`flex h-7 items-center gap-1.5 rounded-md px-3 text-xs font-medium transition-colors ${
                viewMode === m
                  ? "bg-[var(--pf-border-light)] text-[var(--pf-accent-text)]"
                  : "text-[var(--pf-muted)] hover:text-[var(--pf-text)]"
              }`}
            >
              {m === "desktop" ? <Monitor className="h-3.5 w-3.5" /> : <Smartphone className="h-3.5 w-3.5" />}
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {TEMPLATES.map((t, i) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.3 }}
            onMouseEnter={() => setHoveredCard(t.id)}
            onMouseLeave={() => setHoveredCard(null)}
            onClick={() => setSelected(t.id === selected ? null : t.id)}
            className={`group relative cursor-pointer overflow-hidden rounded-xl border transition-all duration-200 ${
              selected === t.id
                ? "border-[var(--pf-accent)] shadow-[0_0_0_1px_var(--pf-accent),0_0_24px_var(--pf-border-light)]"
                : "border-[var(--pf-accent-soft)] hover:border-[var(--pf-border-hover)]"
            }`}
          >
            {}
            <div
              className="relative overflow-hidden"
              style={{
                background: t.bg,
                height: viewMode === "mobile" ? "240px" : "180px",
              }}
            >
              {}
              <div
                className="flex h-7 items-center gap-1.5 px-3"
                style={{ background: t.preview.nav }}
              >
                <div className="h-2 w-2 rounded-full bg-red-500 opacity-70" />
                <div className="h-2 w-2 rounded-full bg-yellow-500 opacity-70" />
                <div className="h-2 w-2 rounded-full bg-green-500 opacity-70" />
                <div
                  className="ml-2 h-3 flex-1 max-w-[120px] rounded-full"
                  style={{ background: `${t.accent}22` }}
                />
              </div>

              {}
              <div
                className="mx-3 mt-2 rounded-lg p-4"
                style={{ background: t.preview.hero }}
              >
                <div
                  className="mb-1.5 h-3 w-3/4 rounded-full"
                  style={{ background: t.accent, opacity: 0.6 }}
                />
                <div
                  className="h-2 w-1/2 rounded-full"
                  style={{ background: t.secondary, opacity: 0.3 }}
                />
              </div>

              {}
              <div className="mx-3 mt-2 flex gap-2">
                {[60, 80, 70].map((w, ci) => (
                  <div
                    key={ci}
                    className="flex-1 rounded-lg p-2"
                    style={{ background: t.preview.card }}
                  >
                    <div
                      className="mb-1 h-1.5 rounded-full"
                      style={{ width: `${w}%`, background: t.accent, opacity: 0.4 }}
                    />
                    <div
                      className="h-1 rounded-full"
                      style={{ width: "50%", background: t.secondary, opacity: 0.2 }}
                    />
                  </div>
                ))}
              </div>

              {}
              <motion.div
                animate={{ opacity: hoveredCard === t.id || selected === t.id ? 1 : 0 }}
                className="absolute inset-0 flex items-center justify-center bg-black/40"
              >
                <span
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-white"
                  style={{ background: t.accent }}
                >
                  {selected === t.id ? "Selected ✓" : "Select"}
                </span>
              </motion.div>

              {}
              {selected === t.id && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-[var(--pf-accent)]"
                >
                  <Check className="h-3.5 w-3.5 text-white" />
                </motion.div>
              )}
            </div>

            {}
            <div className="bg-[var(--pf-surface)] p-4 space-y-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-[var(--pf-text)]">{t.name}</h3>
                  <div className="flex gap-1">
                    {t.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full border border-[var(--pf-border-light)] px-1.5 py-0.5 text-[10px] text-[var(--pf-muted)]"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="mt-0.5 text-xs text-[var(--pf-muted)]">{t.tagline}</p>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleUse(t.id);
                }}
                className="flex w-full items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-semibold transition-colors"
                style={{
                  background: `${t.accent}22`,
                  color: t.accent,
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = `${t.accent}44`;
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = `${t.accent}22`;
                }}
              >
                Use {t.name}
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      {}
      <AnimatePresence>
        {selected && (() => {
          const t = TEMPLATES.find((x) => x.id === selected)!;
          return (
            <motion.div
              key={selected}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.22 }}
              className="rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] p-6"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <h2 className="text-lg font-bold text-[var(--pf-text)]">{t.name}</h2>
                  <p className="mt-1 text-sm text-[var(--pf-muted)]">{t.description}</p>
                </div>
                <button
                  onClick={() => setSelected(null)}
                  className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg text-[var(--pf-muted)] hover:text-[var(--pf-text)]"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
                {t.features.map((f) => (
                  <div key={f} className="flex items-center gap-2 text-sm text-[var(--pf-muted)]">
                    <div
                      className="h-1.5 w-1.5 flex-shrink-0 rounded-full"
                      style={{ background: t.accent }}
                    />
                    {f}
                  </div>
                ))}
              </div>

              <div className="mt-5 flex gap-3">
                <button
                  onClick={() => handleUse(t.id)}
                  className="flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-colors"
                  style={{ background: t.accent }}
                >
                  Use {t.name} template
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </motion.div>
          );
        })()}
      </AnimatePresence>
    </div>
  );
}
