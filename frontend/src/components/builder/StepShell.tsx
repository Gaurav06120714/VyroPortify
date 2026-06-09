"use client";

import { motion } from "framer-motion";

interface Props {
  step: number;
  total: number;
  emoji?: string;
  question: string;
  hint?: string;
  children: React.ReactNode;
  onNext: () => void;
  onBack?: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  loading?: boolean;
}

export default function StepShell({
  step,
  total,
  emoji,
  question,
  hint,
  children,
  onNext,
  onBack,
  nextLabel = "Continue →",
  nextDisabled = false,
  loading = false,
}: Props) {
  const progress = (step / total) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className="flex flex-col gap-8"
    >
      {}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-[var(--pf-muted)]">
          <span>Step {step} of {total}</span>
          <span>{Math.round(progress)}% complete</span>
        </div>
        <div className="h-1 w-full overflow-hidden rounded-full bg-[var(--pf-border-dim)]">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-[var(--pf-accent)] to-[#00d4ff]"
            initial={false}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          />
        </div>
      </div>

      {}
      <div>
        {emoji && <div className="mb-3 text-3xl">{emoji}</div>}
        <h2 className="text-2xl font-bold leading-snug text-[var(--pf-text)] sm:text-3xl">
          {question}
        </h2>
        {hint && <p className="mt-2 text-[var(--pf-muted)]">{hint}</p>}
      </div>

      {}
      <div>{children}</div>

      {}
      <div className="flex items-center gap-3 pt-2">
        {onBack && (
          <button
            onClick={onBack}
            className="rounded-xl border border-[var(--pf-border-light)] px-5 py-2.5 text-sm text-[var(--pf-muted)] hover:border-[rgba(108,99,255,0.5)] hover:text-[var(--pf-text)] transition-colors"
          >
            ← Back
          </button>
        )}
        <button
          onClick={onNext}
          disabled={nextDisabled || loading}
          className="flex items-center gap-2 rounded-xl bg-[var(--pf-accent)] px-6 py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_var(--pf-border-medium)] transition-all hover:bg-[var(--pf-accent-hover)] hover:shadow-[0_0_28px_var(--pf-border-hover)] disabled:opacity-50"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Building your resume…
            </>
          ) : (
            nextLabel
          )}
        </button>
      </div>
    </motion.div>
  );
}
