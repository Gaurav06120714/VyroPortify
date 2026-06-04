"use client";

import { useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import { Toaster } from "sonner";
import { CommandPalette } from "@/components/CommandPalette";
import { KeyboardShortcutsSheet } from "@/components/KeyboardShortcutsSheet";
import { initPostHog, identifyUser, resetPostHog } from "@/lib/posthog";
import { initSentry, setUser, clearUser } from "@/lib/sentry";

export default function Providers({ children }: { children: React.ReactNode }) {
  const { user, isLoaded } = useUser();

  // Initialize analytics & error tracking on mount
  useEffect(() => {
    initPostHog();
    initSentry();
  }, []);

  // Identify user when auth state changes
  useEffect(() => {
    if (!isLoaded) return;

    if (user) {
      identifyUser(user.id, {
        email: user.primaryEmailAddress?.emailAddress,
        name: user.fullName,
      });
      setUser(user.id, user.primaryEmailAddress?.emailAddress);
    } else {
      resetPostHog();
      clearUser();
    }
  }, [user, isLoaded]);

  return (
    <>
      {children}
      <Toaster
        position="top-right"
        richColors
        closeButton
        toastOptions={{
          // Apply our token-based styling on top of the sonner default.
          className: "border border-[var(--border)]",
        }}
      />
      <CommandPalette />
      <KeyboardShortcutsSheet />
    </>
  );
}
