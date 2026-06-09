"use client";

import { useState } from "react";
import Link from "next/link";
import { Check, Zap } from "lucide-react";
import FadeUp from "./FadeUp";

const PLANS = [
  {
    id: "free",
    name: "Free",
    monthlyPrice: 0,
    yearlyPrice: 0,
    desc: "Good for getting started",
    cta: "Start for free",
    href: "/register",
    accent: "#5555aa",
    featured: false,
    perks: [
      "1 portfolio",
      "3 template choices",
      "vyroportify.com/[slug] URL",
      "PDF export",
      "Community support",
    ],
    missing: ["Custom domain", "Analytics", "Priority generation", "Remove branding"],
  },
  {
    id: "pro",
    name: "Pro",
    monthlyPrice: 9,
    yearlyPrice: 7,
    desc: "Best if you're actively job hunting",
    cta: "Get Pro",
    href: "/register?plan=pro",
    accent: "var(--pf-accent)",
    featured: true,
    perks: [
      "Unlimited portfolios",
      "All 3 templates",
      "Custom domain",
      "Analytics dashboard",
      "Priority generation",
      "Remove branding",
      "PDF export",
      "Priority support",
    ],
    missing: [],
  },
  {
    id: "lifetime",
    name: "Lifetime",
    monthlyPrice: 149,
    yearlyPrice: 149,
    desc: "Pay once, own it forever",
    cta: "Get Lifetime",
    href: "/register?plan=lifetime",
    accent: "#00d4ff",
    featured: false,
    perks: [
      "Everything in Pro",
      "Lifetime access",
      "All future templates",
      "Early access to new features",
      "Dedicated support",
    ],
    missing: [],
  },
];

export default function PricingSection() {
  const [yearly, setYearly] = useState(false);

  return (
    <section id="pricing" className="relative px-6 py-28">
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary opacity-[0.04] blur-3xl" />

      <div className="mx-auto max-w-6xl">
        <FadeUp className="mb-12 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-primary">
            Pricing
          </div>
          <h2 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl">
            Pricing
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
            Start free. Upgrade if you need a custom domain or analytics. No hidden fees.
          </p>

          {}
          <div className="mt-8 inline-flex items-center gap-3 rounded-full border border-border bg-card p-1">
            <button
              onClick={() => setYearly(false)}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition-all ${
                !yearly
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setYearly(true)}
              className={`flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold transition-all ${
                yearly
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Yearly
              <span className="rounded-full bg-green-500/15 px-2 py-0.5 text-[10px] font-bold text-green-600 dark:text-green-400">
                SAVE 22%
              </span>
            </button>
          </div>
        </FadeUp>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {PLANS.map((plan, i) => (
            <FadeUp key={plan.id} delay={i * 0.1}>
              <div
                className={`relative flex h-full flex-col rounded-2xl border p-7 transition-all duration-300 ${
                  plan.featured
                    ? "border-primary bg-card shadow-2xl shadow-primary/10"
                    : "border-border bg-card hover:border-primary/30"
                }`}
              >
                {plan.featured && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <div className="flex items-center gap-1.5 rounded-full bg-primary px-3 py-1 text-xs font-bold text-primary-foreground shadow-lg shadow-primary/30">
                      <Zap className="h-3 w-3" /> Most popular
                    </div>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-lg font-bold text-foreground">{plan.name}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{plan.desc}</p>
                  <div className="mt-5 flex items-end gap-1">
                    <span className="text-4xl font-extrabold text-foreground">
                      {plan.id === "lifetime"
                        ? `$${plan.monthlyPrice}`
                        : `$${yearly ? plan.yearlyPrice : plan.monthlyPrice}`}
                    </span>
                    {plan.id !== "lifetime" && plan.monthlyPrice > 0 && (
                      <span className="mb-1 text-sm text-muted-foreground">/mo</span>
                    )}
                    {plan.id === "lifetime" && (
                      <span className="mb-1 text-sm text-muted-foreground">one-time</span>
                    )}
                  </div>
                  {plan.id === "pro" && yearly && (
                    <p className="mt-1 text-xs text-green-600 dark:text-green-400">Billed annually · saves $24/yr</p>
                  )}
                </div>

                <div className="mb-7 flex-1 space-y-3">
                  {plan.perks.map((perk) => (
                    <div key={perk} className="flex items-start gap-2.5 text-sm text-foreground/80">
                      <Check
                        className="mt-0.5 h-4 w-4 flex-shrink-0"
                        style={{ color: plan.accent }}
                      />
                      {perk}
                    </div>
                  ))}
                  {plan.missing.map((m) => (
                    <div key={m} className="flex items-center gap-2.5 text-sm text-muted-foreground/50 line-through">
                      <div className="h-4 w-4 flex-shrink-0" />
                      {m}
                    </div>
                  ))}
                </div>

                <Link
                  href={plan.href}
                  className={`block w-full rounded-xl py-3 text-center text-sm font-semibold transition-all ${
                    plan.featured
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:bg-primary/90 hover:shadow-xl hover:shadow-primary/30"
                      : "border border-border text-foreground/80 hover:border-primary/50 hover:bg-muted/50"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            </FadeUp>
          ))}
        </div>

        <FadeUp delay={0.35} className="mt-10 text-center text-sm text-muted-foreground/60">
          All plans include SSL, 99.9% uptime SLA, and GDPR-compliant data handling.
        </FadeUp>
      </div>
    </section>
  );
}
