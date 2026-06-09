"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { getPortfolioStatus } from "@/lib/api";
import type { PortfolioStatus } from "@/types";

export type JobPhase =
  | "parsing"
  | "enhancing"
  | "building"
  | "finishing"
  | "done"
  | "failed";

function statusToPhase(status: PortfolioStatus["status"]): JobPhase {
  switch (status) {
    case "queued": return "parsing";
    case "generating": return "enhancing";
    case "published": return "done";
    case "failed": return "failed";
    default: return "parsing";
  }
}

void statusToPhase;

interface UseJobStatusResult {
  phase: JobPhase;
  portfolioStatus: PortfolioStatus | null;
  error: string | null;
}

const POLL_INTERVAL_MS = 3000;

const PHASE_SEQUENCE: JobPhase[] = ["parsing", "enhancing", "building", "finishing"];

export function useJobStatus(jobId: string): UseJobStatusResult {
  const { getToken } = useAuth();
  const [phase, setPhase] = useState<JobPhase>("parsing");
  const [portfolioStatus, setPortfolioStatus] = useState<PortfolioStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const _visualPhaseIdx = useRef(0); void _visualPhaseIdx;
  const stopped = useRef(false);

  const advance = useCallback(() => {
    setPhase((prev) => {
      if (prev === "done" || prev === "failed") return prev;
      const idx = PHASE_SEQUENCE.indexOf(prev as JobPhase);
      const next = PHASE_SEQUENCE[Math.min(idx + 1, PHASE_SEQUENCE.length - 1)];
      return next;
    });
  }, []);

  useEffect(() => {
    stopped.current = false;
    let pollTimer: ReturnType<typeof setTimeout>;
    let visualTimer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      if (stopped.current) return;
      try {
        const token = await getToken();
        if (!token) return;
        const result = await getPortfolioStatus(jobId, token);
        setPortfolioStatus(result);

        if (result.status === "published") {
          setPhase("done");
          stopped.current = true;
          return;
        }
        if (result.status === "failed") {
          setPhase("failed");
          setError("Portfolio generation failed. Please try again.");
          stopped.current = true;
          return;
        }
      } catch {
        
      }

      if (!stopped.current) {
        pollTimer = setTimeout(poll, POLL_INTERVAL_MS);
      }
    };

    const tick = () => {
      if (stopped.current) return;
      advance();
      visualTimer = setTimeout(tick, 5000);
    };
    visualTimer = setTimeout(tick, 5000);

    poll();

    return () => {
      stopped.current = true;
      clearTimeout(pollTimer);
      clearTimeout(visualTimer);
    };
  }, [jobId, getToken, advance]);

  return { phase, portfolioStatus, error };
}
