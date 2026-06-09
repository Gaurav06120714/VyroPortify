"use client";

import Link from "next/link";
import { Zap } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import ThemeToggle from "@/components/ThemeToggle";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { isLight } = useTheme();

  return (
    <div
      className="relative flex min-h-dvh flex-col items-center justify-center transition-colors duration-300"
      style={{ background: isLight ? "#f5f5f7" : "var(--pf-bg)" }}
    >
      {}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute -top-40 -left-40 w-96 h-96 rounded-full blur-3xl"
          style={{ background: "var(--pf-accent)", opacity: isLight ? 0.08 : 0.05 }}
        />
        <div
          className="absolute top-1/2 right-0 w-80 h-80 rounded-full blur-3xl"
          style={{ background: "#00d4ff", opacity: isLight ? 0.06 : 0.05 }}
        />
        <div
          className="absolute bottom-0 left-1/3 w-64 h-64 rounded-full blur-3xl"
          style={{ background: "var(--pf-accent)", opacity: isLight ? 0.06 : 0.05 }}
        />
      </div>

      {}
      <div className="absolute left-0 right-0 top-0 z-20 flex items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--pf-accent)] shadow-[0_0_16px_var(--pf-border-hover)]">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <span
            className="text-lg font-bold transition-colors duration-300"
            style={{ color: isLight ? "#1a1a2e" : "#ffffff" }}
          >
            Portify<span className="text-[var(--pf-accent)]">AI</span>
          </span>
        </Link>
        <ThemeToggle />
      </div>

      {}
      <div className="relative z-10 w-full max-w-md px-4 py-20">{children}</div>
    </div>
  );
}
