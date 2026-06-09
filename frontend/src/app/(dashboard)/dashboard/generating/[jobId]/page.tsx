"use client";

import { useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { FileSearch, Sparkles, Code2, Rocket, AlertCircle } from "lucide-react";
import { useJobStatus, type JobPhase } from "@/hooks/useJobStatus";

const STEPS: { phase: JobPhase; label: string; sublabel: string; icon: React.ReactNode }[] = [
  {
    phase: "parsing",
    label: "Parsing Resume",
    sublabel: "Extracting your experience, skills & projects",
    icon: <FileSearch className="h-6 w-6" />,
  },
  {
    phase: "enhancing",
    label: "Enhancing Content",
    sublabel: "Claude AI is writing your portfolio copy",
    icon: <Sparkles className="h-6 w-6" />,
  },
  {
    phase: "building",
    label: "Building Portfolio",
    sublabel: "Rendering your chosen template",
    icon: <Code2 className="h-6 w-6" />,
  },
  {
    phase: "finishing",
    label: "Almost Ready!",
    sublabel: "Uploading and generating your live URL",
    icon: <Rocket className="h-6 w-6" />,
  },
];

const PHASE_INDEX: Record<JobPhase, number> = {
  parsing: 0,
  enhancing: 1,
  building: 2,
  finishing: 3,
  done: 4,
  failed: -1,
};

interface Props {
  params: Promise<{ jobId: string }>;
}

export default function GeneratingPage({ params }: Props) {
  const { jobId } = use(params);
  const router = useRouter();
  const { phase, portfolioStatus, error } = useJobStatus(jobId);

  useEffect(() => {
    if (phase === "done" && portfolioStatus?.id) {
      if (portfolioStatus.ai_fallback) {
        toast.warning("AI enhancement partially failed. Using standard copy instead.", {
          duration: 5000,
        });
      }
      const timer = setTimeout(() => {
        router.push(`/dashboard/portfolio/${portfolioStatus.id}/preview`);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [phase, portfolioStatus, router]);

  const currentIdx = PHASE_INDEX[phase] ?? 0;

  return (
    <div className="flex min-h-full flex-col items-center justify-center px-4 py-16">
      {}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <motion.div
          className="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--pf-accent)]"
          animate={{ scale: [1, 1.15, 1], opacity: [0.04, 0.07, 0.04] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <div className="relative w-full max-w-md space-y-10 text-center">
        {}
        <AnimatePresence mode="wait">
          <motion.div
            key={phase}
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.7, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-[var(--pf-accent-soft)]"
          >
            {error ? (
              <AlertCircle className="h-9 w-9 text-red-400" />
            ) : phase === "done" ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 260, damping: 20 }}
              >
                <Rocket className="h-9 w-9 text-[var(--pf-accent)]" />
              </motion.div>
            ) : (
              <motion.div
                animate={{ rotate: phase === "building" ? [0, 5, -5, 0] : 0 }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="text-[var(--pf-accent)]"
              >
                {STEPS[Math.min(currentIdx, 3)]?.icon}
              </motion.div>
            )}
          </motion.div>
        </AnimatePresence>

        {}
        <AnimatePresence mode="wait">
          <motion.div
            key={phase}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            {error ? (
              <>
                <h1 className="text-2xl font-bold text-red-400">Generation Failed</h1>
                <p className="mt-2 text-[var(--pf-muted)]">{error}</p>
                <button
                  onClick={() => router.push("/dashboard/upload")}
                  className="mt-6 rounded-xl bg-[var(--pf-accent)] px-6 py-2.5 text-sm font-semibold text-white hover:bg-[var(--pf-accent-hover)] transition-colors"
                >
                  Try again
                </button>
              </>
            ) : phase === "done" ? (
              <>
                <h1 className="text-2xl font-bold text-[var(--pf-text)]">Your portfolio is ready!</h1>
                <p className="mt-2 text-[var(--pf-muted)]">Redirecting you now…</p>
              </>
            ) : (
              <>
                <h1 className="text-2xl font-bold text-[var(--pf-text)]">
                  {STEPS[Math.min(currentIdx, 3)]?.label}
                </h1>
                <p className="mt-2 text-[var(--pf-muted)]">
                  {STEPS[Math.min(currentIdx, 3)]?.sublabel}
                </p>
              </>
            )}
          </motion.div>
        </AnimatePresence>

        {}
        {!error && (
          <div className="space-y-3">
            {STEPS.map((step, idx) => {
              const isDone = idx < currentIdx || phase === "done";
              const isActive = idx === currentIdx && phase !== "done";
              return (
                <motion.div
                  key={step.phase}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.07, duration: 0.3 }}
                  className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${
                    isActive
                      ? "border-[var(--pf-accent)] bg-[var(--pf-border-dim)]"
                      : isDone
                        ? "border-[rgba(34,197,94,0.25)] bg-[rgba(34,197,94,0.05)]"
                        : "border-[var(--pf-border-dim)] bg-[var(--pf-surface)] opacity-40"
                  }`}
                >
                  {}
                  <div
                    className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg ${
                      isActive
                        ? "bg-[var(--pf-border-light)] text-[var(--pf-accent)]"
                        : isDone
                          ? "bg-[rgba(34,197,94,0.15)] text-green-400"
                          : "bg-[var(--pf-border-subtle)] text-[var(--pf-muted)]"
                    }`}
                  >
                    {isDone ? (
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 300 }}
                        className="text-sm font-bold"
                      >
                        ✓
                      </motion.span>
                    ) : (
                      <span className={isActive ? "animate-pulse" : ""}>{step.icon}</span>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-semibold ${
                        isActive
                          ? "text-[var(--pf-text)]"
                          : isDone
                            ? "text-green-400"
                            : "text-[var(--pf-muted)]"
                      }`}
                    >
                      {step.label}
                    </p>
                    {isActive && (
                      <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-xs text-[var(--pf-muted)] mt-0.5"
                      >
                        {step.sublabel}
                      </motion.p>
                    )}
                  </div>

                  {}
                  {isActive && (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
                      className="h-4 w-4 rounded-full border-2 border-[var(--pf-accent)] border-t-transparent flex-shrink-0"
                    />
                  )}
                </motion.div>
              );
            })}
          </div>
        )}

        {}
        {!error && phase !== "done" && (
          <div className="h-1 w-full overflow-hidden rounded-full bg-[var(--pf-border-dim)]">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-[var(--pf-accent)] to-[#00d4ff]"
              initial={{ width: "5%" }}
              animate={{
                width: `${Math.max(5, ((currentIdx + 1) / STEPS.length) * 100)}%`,
              }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>
        )}

        <p className="text-xs text-[var(--pf-muted)]">Job ID: {jobId}</p>
      </div>
    </div>
  );
}
