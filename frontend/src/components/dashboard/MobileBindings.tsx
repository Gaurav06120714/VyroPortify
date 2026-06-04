"use client";

import { BottomTabNav } from "@/components/dashboard/BottomTabNav";
import { useSwipeBack } from "@/hooks/useSwipeBack";

/**
 * Client-only mount point for the v2.2.2 mobile bindings — the
 * dashboard layout itself stays a Server Component, this single
 * "use client" file hosts both the tab nav and the swipe-back hook.
 */
export function MobileBindings() {
  useSwipeBack();
  return <BottomTabNav />;
}
