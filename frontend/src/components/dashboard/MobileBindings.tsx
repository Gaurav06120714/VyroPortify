"use client";

import { BottomTabNav } from "@/components/dashboard/BottomTabNav";
import { useSwipeBack } from "@/hooks/useSwipeBack";

export function MobileBindings() {
  useSwipeBack();
  return <BottomTabNav />;
}
