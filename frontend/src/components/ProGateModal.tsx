"use client";

import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { X, Zap, Check } from "lucide-react";

const PRO_PERKS = [
  "Unlimited portfolios",
  "All 3 premium templates",
  "AI skill suggestions",
  "Custom domain support",
  "Priority generation queue",
  "Remove VyroPortify branding",
];

interface Props {
  open: boolean;
  onClose: () => void;
  featureName?: string;
}

export default function ProGateModal({ open, onClose, featureName }: Props) {
  const router = useRouter();

  return (
    <AnimatePresence>
      {open && (
        <>
          {}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
          />

          {}
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.93, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.93, y: 16 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="relative w-full max-w-md overflow-hidden rounded-2xl border border-[var(--pf-border-hover)] bg-[var(--pf-surface)] shadow-[0_0_80px_var(--pf-accent-soft)]">
              {}
              <div className="h-1 w-full bg-gradient-to-r from-[var(--pf-accent)] to-[#00d4ff]" />

              {}
              <button
                onClick={onClose}
                className="absolute right-4 top-4 flex h-7 w-7 items-center justify-center rounded-lg text-[var(--pf-muted)] hover:bg-[var(--pf-border-dim)] hover:text-[var(--pf-text)] transition-colors"
              >
                <X className="h-4 w-4" />
              </button>

              <div className="p-7">
                {}
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--pf-accent-soft)]">
                  <Zap className="h-6 w-6 text-[var(--pf-accent)]" />
                </div>

                {}
                <h2 className="text-xl font-bold text-[var(--pf-text)]">
                  {featureName
                    ? `"${featureName}" is a Pro feature`
                    : "Upgrade to VyroPortify Pro"}
                </h2>
                <p className="mt-1.5 text-sm text-[var(--pf-muted)]">
                  Get unlimited portfolios, all templates, and AI-powered features for{" "}
                  <span className="font-semibold text-[var(--pf-text)]">$9/month</span>.
                </p>

                {}
                <ul className="mt-5 space-y-2">
                  {PRO_PERKS.map((perk) => (
                    <li key={perk} className="flex items-center gap-2.5 text-sm text-[var(--pf-text)]">
                      <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-[var(--pf-accent-soft)]">
                        <Check className="h-3 w-3 text-[var(--pf-accent)]" />
                      </div>
                      {perk}
                    </li>
                  ))}
                </ul>

                {}
                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => { onClose(); router.push("/pricing"); }}
                    className="flex-1 rounded-xl bg-[var(--pf-accent)] py-3 text-sm font-semibold text-white shadow-[0_0_24px_var(--pf-border-hover)] hover:bg-[var(--pf-accent-hover)] transition-colors"
                  >
                    Upgrade to Pro — $9/mo
                  </button>
                  <button
                    onClick={onClose}
                    className="rounded-xl border border-[var(--pf-border-light)] px-4 py-3 text-sm text-[var(--pf-muted)] hover:text-[var(--pf-text)] transition-colors"
                  >
                    Maybe later
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
