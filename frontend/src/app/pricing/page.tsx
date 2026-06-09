"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Check, Zap, ArrowRight, Loader2 } from "lucide-react";
import { createCheckoutSession, ApiError } from "@/lib/api";
import { usePlan } from "@/context/PlanContext";
import { useTheme } from "@/context/ThemeContext";
import ThemeToggle from "@/components/ThemeToggle";
import ProfileDropdown from "@/components/ProfileDropdown";

const FREE_FEATURES = [
  "3 portfolios",
  "Aurora template only",
  "Standard generation queue",
  "VyroPortify branding",
  "Public portfolio URL",
];

const PRO_FEATURES = [
  "Unlimited portfolios",
  "All 3 premium templates",
  "AI skill suggestions",
  "Priority generation queue",
  "Remove VyroPortify branding",
  "Custom domain support",
  "Early access to new features",
];

const FAQS = [
  {
    q: "Can I cancel anytime?",
    a: "Yes — cancel from the billing portal in settings. You keep Pro until the end of the billing period.",
  },
  {
    q: "Is there a free trial?",
    a: "The Free plan lets you try the core features indefinitely. No credit card required.",
  },
  {
    q: "What payment methods do you accept?",
    a: "All major credit/debit cards, Apple Pay, and Google Pay via Stripe.",
  },
  {
    q: "Can I switch templates after generating?",
    a: "Yes — on Pro you can regenerate your portfolio with any template at any time.",
  },
];

export default function PricingPage() {
  const { isSignedIn, getToken } = useAuth();
  const { plan } = usePlan();
  const { isLight } = useTheme();
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    if (!isSignedIn) {
      router.push("/register?redirect=/pricing");
      return;
    }
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      const res = await createCheckoutSession(token);
      window.location.href = res.checkout_url;
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Could not start checkout. Try again.";
      toast.error(msg);
      setLoading(false);
    }
  };

  const bg = isLight ? "#ffffff" : "var(--pf-bg)";
  const cardBg = isLight ? "#f8f8fa" : "var(--pf-surface)";
  const border = isLight ? "rgba(0,0,0,0.08)" : "var(--pf-accent-soft)";
  const heading = isLight ? "#1a1a2e" : "var(--pf-text)";
  const sub = isLight ? "#666688" : "var(--pf-muted)";
  const text = isLight ? "#333" : "#c8c8e8";

  return (
    <div className="min-h-dvh transition-colors duration-300" style={{ background: bg, color: heading }}>
      {}
      <nav
        className="sticky top-0 z-50 border-b backdrop-blur-md transition-colors duration-300"
        style={{
          background: isLight ? "rgba(255,255,255,0.85)" : "rgba(13,13,20,0.85)",
          borderColor: border,
        }}
      >
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--pf-accent)]">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold" style={{ color: heading }}>
              Portify<span className="text-[var(--pf-accent)]">AI</span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle compact />
            {isSignedIn ? (
              <ProfileDropdown />
            ) : (
              <>
                <Link
                  href="/login"
                  className="hidden text-sm font-medium transition-colors sm:block"
                  style={{ color: sub }}
                >
                  Sign in
                </Link>
                <Link
                  href="/register"
                  className="rounded-lg bg-[var(--pf-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--pf-accent-hover)] transition-colors"
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-5xl px-4 py-20 space-y-20">
        {}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="text-center space-y-4"
        >
          <h1 className="text-4xl font-extrabold sm:text-5xl" style={{ color: heading }}>
            Simple,{" "}
            <span className="bg-gradient-to-r from-[var(--pf-accent)] to-[#00d4ff] bg-clip-text text-transparent">
              honest pricing
            </span>
          </h1>
          <p className="text-lg" style={{ color: sub }}>
            Start free. Upgrade when you&apos;re ready.
          </p>
        </motion.div>

        {}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 md:items-start">
          {}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05, duration: 0.3 }}
            className="rounded-2xl border p-7 transition-colors duration-300"
            style={{ background: cardBg, borderColor: border }}
          >
            <div className="mb-6">
              <p className="text-sm font-semibold uppercase tracking-wider" style={{ color: sub }}>
                Free
              </p>
              <div className="mt-2 flex items-end gap-1">
                <span className="text-4xl font-extrabold" style={{ color: heading }}>$0</span>
                <span className="mb-1" style={{ color: sub }}>/month</span>
              </div>
              <p className="mt-1 text-sm" style={{ color: sub }}>
                Forever free. No credit card needed.
              </p>
            </div>

            <ul className="space-y-3 mb-7">
              {FREE_FEATURES.map((f) => (
                <li key={f} className="flex items-center gap-2.5 text-sm" style={{ color: sub }}>
                  <Check className="h-4 w-4 flex-shrink-0" style={{ color: sub }} />
                  {f}
                </li>
              ))}
            </ul>

            {plan === "free" ? (
              <div
                className="w-full rounded-xl border py-2.5 text-center text-sm font-semibold"
                style={{ borderColor: border, color: sub }}
              >
                Current plan
              </div>
            ) : (
              <Link
                href="/dashboard"
                className="block w-full rounded-xl border py-2.5 text-center text-sm font-semibold transition-colors hover:opacity-80"
                style={{ borderColor: border, color: sub }}
              >
                Go to dashboard
              </Link>
            )}
          </motion.div>

          {}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
            className="relative overflow-hidden rounded-2xl border p-7 shadow-lg transition-colors duration-300"
            style={{
              background: cardBg,
              borderColor: "var(--pf-accent)",
              boxShadow: "0 0 40px var(--pf-accent-subtle)",
            }}
          >
            {}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
              <span className="rounded-full bg-[var(--pf-accent)] px-4 py-1 text-xs font-bold text-white shadow-md">
                MOST POPULAR
              </span>
            </div>

            {}
            <div className="absolute left-0 right-0 top-0 h-[2px] bg-gradient-to-r from-[var(--pf-accent)] to-[#00d4ff]" />

            <div className="mb-6 pt-2">
              <p className="text-sm font-semibold uppercase tracking-wider text-[var(--pf-accent)]">Pro</p>
              <div className="mt-2 flex items-end gap-1">
                <span className="text-4xl font-extrabold" style={{ color: heading }}>$9</span>
                <span className="mb-1" style={{ color: sub }}>/month</span>
              </div>
              <p className="mt-1 text-sm" style={{ color: sub }}>
                Everything you need to stand out.
              </p>
            </div>

            <ul className="space-y-3 mb-7">
              {PRO_FEATURES.map((f) => (
                <li key={f} className="flex items-center gap-2.5 text-sm" style={{ color: text }}>
                  <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-[var(--pf-accent-soft)]">
                    <Check className="h-3 w-3 text-[var(--pf-accent)]" />
                  </div>
                  {f}
                </li>
              ))}
            </ul>

            {plan === "pro" ? (
              <Link
                href="/dashboard/settings/billing"
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-green-500/40 bg-green-500/8 py-3 text-sm font-semibold text-green-600"
              >
                <Check className="h-4 w-4" /> Active plan — Manage
              </Link>
            ) : (
              <button
                onClick={handleUpgrade}
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--pf-accent)] py-3 text-sm font-semibold text-white shadow-[0_0_24px_var(--pf-border-hover)] hover:bg-[var(--pf-accent-hover)] hover:shadow-[0_0_32px_rgba(108,99,255,0.5)] transition-all disabled:opacity-60"
              >
                {loading ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Redirecting&hellip;</>
                ) : (
                  <>Upgrade to Pro <ArrowRight className="h-4 w-4" /></>
                )}
              </button>
            )}

            <p className="mt-3 text-center text-xs" style={{ color: sub }}>
              Cancel anytime &middot; Powered by Stripe
            </p>
          </motion.div>
        </div>

        {}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.3 }}
          className="space-y-6"
        >
          <h2 className="text-center text-2xl font-bold" style={{ color: heading }}>
            Frequently asked questions
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {FAQS.map(({ q, a }) => (
              <div
                key={q}
                className="rounded-xl border p-5 transition-colors duration-300"
                style={{ background: cardBg, borderColor: border }}
              >
                <p className="font-semibold" style={{ color: heading }}>{q}</p>
                <p className="mt-1.5 text-sm" style={{ color: sub }}>{a}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.3 }}
          className="text-center space-y-4 pb-8"
        >
          <p style={{ color: sub }}>Still unsure? Try the Free plan — no card required.</p>
          <Link
            href={isSignedIn ? "/dashboard" : "/register"}
            className="inline-flex items-center gap-2 rounded-xl border px-6 py-3 text-sm font-semibold transition-colors hover:opacity-80"
            style={{ borderColor: border, color: heading }}
          >
            Start free <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
