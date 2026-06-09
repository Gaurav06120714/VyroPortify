"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const EDGE_WIDTH = 24;
const MIN_DISTANCE = 80;

export function useSwipeBack() {
  const router = useRouter();

  useEffect(() => {
    let startX = 0;
    let startY = 0;
    let active = false;

    function onTouchStart(e: TouchEvent) {
      const t = e.touches[0];
      if (!t || t.clientX > EDGE_WIDTH) return;
      startX = t.clientX;
      startY = t.clientY;
      active = true;
    }

    function onTouchEnd(e: TouchEvent) {
      if (!active) return;
      active = false;
      const t = e.changedTouches[0];
      if (!t) return;
      const dx = t.clientX - startX;
      const dy = Math.abs(t.clientY - startY);
      if (dx > MIN_DISTANCE && dx > dy && history.length > 1) {
        router.back();
      }
    }

    document.addEventListener("touchstart", onTouchStart, { passive: true });
    document.addEventListener("touchend", onTouchEnd, { passive: true });
    return () => {
      document.removeEventListener("touchstart", onTouchStart);
      document.removeEventListener("touchend", onTouchEnd);
    };
  }, [router]);
}
