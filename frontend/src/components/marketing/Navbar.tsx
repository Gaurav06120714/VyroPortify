"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import { Zap, Menu, X } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import ThemeToggle from "@/components/ThemeToggle";
import ProfileDropdown from "@/components/ProfileDropdown";

const LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#templates", label: "Templates" },
  { href: "#features", label: "Features" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { isLight } = useTheme();
  const { user, isLoaded } = useUser();

  useEffect(() => {
    const handler = () => { if (window.innerWidth >= 768) setMobileOpen(false); };
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const isSignedIn = isLoaded && !!user;

  return (
    <header className="fixed top-0 z-50 w-full">
      <div
        className="absolute inset-0 border-b transition-colors duration-300"
        style={{
          opacity: scrolled ? 1 : 0,
          background: isLight ? "rgba(245,245,247,0.92)" : "rgba(15,15,26,0.92)",
          borderColor: isLight ? "rgba(0,0,0,0.06)" : "var(--pf-border-dim)",
        }}
      />

      <nav className="relative mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {}
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--pf-accent)]">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <span
            className="text-lg font-bold tracking-tight transition-colors duration-300"
            style={{ color: isLight ? "#1a1a2e" : "#ffffff" }}
          >
            Portify<span className="text-[var(--pf-accent)]">AI</span>
          </span>
        </Link>

        {}
        <div className="hidden items-center gap-1 md:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="rounded-lg px-3.5 py-2 text-sm font-medium transition-colors"
              style={{ color: isLight ? "#666688" : "#9999bb" }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = isLight ? "#1a1a2e" : "#ffffff";
                e.currentTarget.style.background = isLight
                  ? "var(--pf-border-faint)"
                  : "var(--pf-border-subtle)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = isLight ? "#666688" : "#9999bb";
                e.currentTarget.style.background = "transparent";
              }}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {}
        <div className="hidden items-center gap-3 md:flex">
          <ThemeToggle compact />

          {!isLoaded ? (
            <div className="flex items-center gap-2">
              <div
                className="h-8 w-8 rounded-full"
                style={{ background: isLight ? "#e5e5ea" : "var(--pf-accent-soft)" }}
              />
              <div
                className="h-4 w-16 rounded"
                style={{ background: isLight ? "#e5e5ea" : "var(--pf-accent-soft)" }}
              />
            </div>
          ) : isSignedIn ? (
            <ProfileDropdown />
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-medium transition-colors"
                style={{ color: isLight ? "#666688" : "#9999bb" }}
                onMouseEnter={(e) => { e.currentTarget.style.color = isLight ? "#1a1a2e" : "#ffffff"; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = isLight ? "#666688" : "#9999bb"; }}
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-xl bg-[var(--pf-accent)] px-4 py-2 text-sm font-semibold text-white transition-all hover:bg-[var(--pf-accent-hover)]"
              >
                Get started free
              </Link>
            </>
          )}
        </div>

        {}
        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle compact />
          {isSignedIn && <ProfileDropdown />}
          <button
            onClick={() => setMobileOpen((v) => !v)}
            className="rounded-lg p-2 transition-colors"
            style={{ color: isLight ? "#666688" : "#9999bb" }}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {}
      {mobileOpen && (
        <div
          className="relative overflow-hidden border-b md:hidden"
          style={{
            background: isLight ? "#f5f5f7" : "#0F0F1A",
            borderColor: isLight ? "rgba(0,0,0,0.06)" : "var(--pf-accent-subtle)",
          }}
        >
          <div className="px-6 pb-6 pt-2">
            {LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setMobileOpen(false)}
                className="block py-3 text-sm font-medium transition-colors"
                style={{ color: isLight ? "#666688" : "#9999bb" }}
              >
                {l.label}
              </Link>
            ))}
            {!isSignedIn && (
              <div className="mt-4 flex flex-col gap-3">
                <Link
                  href="/login"
                  className="text-center text-sm font-medium"
                  style={{ color: isLight ? "#666688" : "#9999bb" }}
                >
                  Sign in
                </Link>
                <Link
                  href="/register"
                  className="rounded-xl bg-[var(--pf-accent)] py-2.5 text-center text-sm font-semibold text-white"
                >
                  Get started free
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
