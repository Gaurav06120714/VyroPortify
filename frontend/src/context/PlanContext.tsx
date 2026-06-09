"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { getBillingStatus } from "@/lib/api";

interface PlanContextValue {
  plan: "free" | "pro";
  loading: boolean;
  refresh: () => Promise<void>;
}

const PlanContext = createContext<PlanContextValue>({
  plan: "free",
  loading: true,
  refresh: async () => {},
});

export function PlanProvider({ children }: { children: React.ReactNode }) {
  const { getToken, isSignedIn } = useAuth();
  const [plan, setPlan] = useState<"free" | "pro">("free");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!isSignedIn) { setLoading(false); return; }
    try {
      const token = await getToken();
      if (!token) return;
      const status = await getBillingStatus(token);
      setPlan(status.plan === "pro" ? "pro" : "free");
    } catch {
      
    } finally {
      setLoading(false);
    }
  }, [getToken, isSignedIn]);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <PlanContext.Provider value={{ plan, loading, refresh }}>
      {children}
    </PlanContext.Provider>
  );
}

export function usePlan() {
  return useContext(PlanContext);
}
