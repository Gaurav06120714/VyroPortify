"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  Zap,
  CheckCircle,
  ExternalLink,
  ArrowRight,
  Loader2,
  CreditCard,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { getBillingStatus, createCheckoutSession, getPortalUrl, ApiError } from "@/lib/api";
import { usePlan } from "@/context/PlanContext";

interface BillingStatus {
  plan: string;
  stripe_customer_id: string | null;
  subscription_status: string | null;
  current_period_end: number | null;
  cancel_at_period_end: boolean | null;
}

function BillingPageInner() {
  const { getToken } = useAuth();
  const { plan, refresh: refreshPlan } = usePlan();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    if (searchParams.get("success") === "1") {
      toast.success("🎉 Welcome to Pro! Your plan has been upgraded.");
      refreshPlan();
      
      router.replace("/dashboard/settings/billing");
    }
    if (searchParams.get("cancelled") === "1") {
      toast.info("Checkout cancelled — your plan was not changed.");
      router.replace("/dashboard/settings/billing");
    }
  }, [searchParams, refreshPlan, router]);

  const fetchStatus = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const s = await getBillingStatus(token);
      setStatus(s);
    } catch {
      toast.error("Could not load billing status.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStatus(); }, []); 

  const handleUpgrade = async () => {
    setCheckoutLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const res = await createCheckoutSession(token);
      window.location.href = res.checkout_url;
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Could not start checkout.";
      toast.error(msg);
      setCheckoutLoading(false);
    }
  };

  const handlePortal = async () => {
    setPortalLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const res = await getPortalUrl(token);
      window.location.href = res.portal_url;
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Could not open billing portal.";
      toast.error(msg);
      setPortalLoading(false);
    }
  };

  const renewalDate = status?.current_period_end
    ? new Date(status.current_period_end * 1000).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : null;

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--pf-text)]">Billing &amp; Plan</h1>
        <p className="mt-1 text-[var(--pf-muted)]">Manage your subscription and payment details.</p>
      </div>

      {}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className={`rounded-xl border p-6 ${
          plan === "pro"
            ? "border-[var(--pf-accent)] bg-[var(--pf-border-faint)] shadow-[0_0_30px_var(--pf-border-subtle)]"
            : "border-[var(--pf-accent-soft)] bg-[var(--pf-surface)]"
        }`}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                plan === "pro" ? "bg-[var(--pf-border-light)]" : "bg-[var(--pf-border-dim)]"
              }`}
            >
              <Zap className={`h-5 w-5 ${plan === "pro" ? "text-[var(--pf-accent)]" : "text-[var(--pf-muted)]"}`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="font-bold text-[var(--pf-text)] text-lg capitalize">{plan} Plan</p>
                {plan === "pro" && (
                  <span className="rounded-full bg-[var(--pf-border-light)] px-2 py-0.5 text-xs font-semibold text-[var(--pf-accent)]">
                    ACTIVE
                  </span>
                )}
              </div>
              <p className="text-sm text-[var(--pf-muted)]">
                {plan === "pro" ? "$9 / month" : "Free forever"}
              </p>
            </div>
          </div>

          {loading && <Loader2 className="h-4 w-4 animate-spin text-[var(--pf-muted)]" />}
        </div>

        {}
        {status && plan === "pro" && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2 rounded-lg bg-[var(--pf-border-subtle)] px-3 py-2.5">
              <CheckCircle className="h-4 w-4 flex-shrink-0 text-green-400" />
              <div>
                <p className="text-xs text-[var(--pf-muted)]">Status</p>
                <p className="text-sm font-medium capitalize text-[var(--pf-text)]">
                  {status.subscription_status ?? "active"}
                </p>
              </div>
            </div>
            {renewalDate && (
              <div className="flex items-center gap-2 rounded-lg bg-[var(--pf-border-subtle)] px-3 py-2.5">
                <Calendar className="h-4 w-4 flex-shrink-0 text-[var(--pf-muted)]" />
                <div>
                  <p className="text-xs text-[var(--pf-muted)]">
                    {status.cancel_at_period_end ? "Cancels" : "Renews"}
                  </p>
                  <p className="text-sm font-medium text-[var(--pf-text)]">{renewalDate}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {status?.cancel_at_period_end && (
          <div className="mt-4 rounded-lg border border-yellow-500/20 bg-yellow-500/5 px-3 py-2 text-sm text-yellow-400">
            Your subscription will cancel at the end of the billing period. You can reactivate it from the portal.
          </div>
        )}
      </motion.div>

      {}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.07, duration: 0.25 }}
        className="space-y-3"
      >
        {plan === "free" ? (
          <div className="rounded-xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-5">
            <h3 className="font-semibold text-[var(--pf-text)]">Upgrade to Pro</h3>
            <p className="mt-1 text-sm text-[var(--pf-muted)]">
              Unlimited portfolios, all templates, AI skill suggestions, and more — for $9/month.
            </p>
            <div className="mt-4 flex gap-3">
              <button
                onClick={handleUpgrade}
                disabled={checkoutLoading}
                className="flex items-center gap-2 rounded-xl bg-[var(--pf-accent)] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[var(--pf-accent-hover)] transition-colors disabled:opacity-60"
              >
                {checkoutLoading ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Redirecting…</>
                ) : (
                  <>Upgrade to Pro <ArrowRight className="h-4 w-4" /></>
                )}
              </button>
              <Link
                href="/pricing"
                className="flex items-center gap-1.5 rounded-xl border border-[var(--pf-border-light)] px-4 py-2.5 text-sm text-[var(--pf-muted)] hover:text-[var(--pf-text)] transition-colors"
              >
                See full comparison
              </Link>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--pf-border-dim)]">
                <CreditCard className="h-4 w-4 text-[var(--pf-accent)]" />
              </div>
              <div>
                <h3 className="font-semibold text-[var(--pf-text)]">Manage subscription</h3>
                <p className="text-sm text-[var(--pf-muted)]">
                  Update payment method, download invoices, or cancel.
                </p>
              </div>
            </div>
            <button
              onClick={handlePortal}
              disabled={portalLoading}
              className="mt-4 flex items-center gap-2 rounded-xl border border-[var(--pf-border-light)] px-4 py-2.5 text-sm font-semibold text-[var(--pf-text)] hover:border-[rgba(108,99,255,0.5)] transition-colors disabled:opacity-60"
            >
              {portalLoading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Opening portal…</>
              ) : (
                <>Open Stripe Portal <ExternalLink className="h-3.5 w-3.5" /></>
              )}
            </button>
          </div>
        )}

        {}
        <button
          onClick={() => { setLoading(true); fetchStatus(); }}
          className="flex items-center gap-1.5 text-xs text-[var(--pf-muted)] hover:text-[var(--pf-text)] transition-colors"
        >
          <RefreshCw className="h-3 w-3" /> Refresh billing status
        </button>
      </motion.div>

      {}
      {plan === "free" && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.14, duration: 0.25 }}
          className="rounded-xl border border-[var(--pf-accent-subtle)] bg-[var(--pf-surface)] p-5"
        >
          <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-[var(--pf-muted)]">
            Pro includes
          </p>
          <div className="grid grid-cols-2 gap-2">
            {[
              "Unlimited portfolios",
              "All 3 templates",
              "AI skill suggestions",
              "Priority queue",
              "No branding",
              "Custom domain",
            ].map((f) => (
              <div key={f} className="flex items-center gap-2 text-sm text-[var(--pf-muted)]">
                <div className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[var(--pf-accent)]" />
                {f}
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={<div className="flex h-40 items-center justify-center"><Loader2 className="h-5 w-5 animate-spin text-[var(--pf-accent)]" /></div>}>
      <BillingPageInner />
    </Suspense>
  );
}
