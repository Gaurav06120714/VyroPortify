"use client";

import { useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import { Toaster } from "sonner";
import { CommandPalette } from "@/components/CommandPalette";
import { KeyboardShortcutsSheet } from "@/components/KeyboardShortcutsSheet";
import { PwaInstallPrompt } from "@/components/PwaInstallPrompt";
import { initPostHog, identifyUser, resetPostHog } from "@/lib/posthog";
import { initSentry, setUser, clearUser } from "@/lib/sentry";

export default function Providers({ children }: { children: React.ReactNode }) {
  const { user, isLoaded } = useUser();

  useEffect(() => {
    initPostHog();
    initSentry();
  }, []);

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
          
          className: "border border-[var(--border)]",
        }}
      />
      <CommandPalette />
      <KeyboardShortcutsSheet />
      <PwaInstallPrompt />
    </>
  );
}
