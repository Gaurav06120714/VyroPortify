"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import {
  Menu,
  X,
  LayoutDashboard,
  Upload,
  FolderOpen,
  Palette,
  Settings,
  Zap,
  PenLine,
  FileText,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/build-resume", label: "AI Resume Builder", icon: PenLine },
  { href: "/dashboard/upload", label: "Upload Resume", icon: Upload },
  { href: "/dashboard/portfolios", label: "My Portfolios", icon: FolderOpen },
  { href: "/dashboard/templates", label: "Templates", icon: Palette },
  { href: "/dashboard/cover-letter", label: "Cover Letter", icon: FileText },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export default function MobileHeader() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <>
      <header className="flex h-16 items-center justify-between border-b border-[var(--pf-accent-soft)] bg-[var(--pf-bg)] px-4 lg:hidden">
        <Link href="/" className="flex items-center gap-2 transition-opacity hover:opacity-80">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--pf-accent)]">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-bold text-[var(--pf-text)]">VyroPortify</span>
        </Link>
        <div className="flex items-center gap-3">
          <UserButton />
          <button
            onClick={() => setOpen(true)}
            className="rounded-lg p-2 text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)]"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </header>

      {}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setOpen(false)}
          />
          <aside className="absolute left-0 top-0 flex h-full w-64 flex-col bg-[var(--pf-bg)] shadow-xl">
            <div className="flex h-16 items-center justify-between border-b border-[var(--pf-accent-soft)] px-4">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--pf-accent)]">
                  <Zap className="h-4 w-4 text-white" />
                </div>
                <span className="font-bold text-[var(--pf-text)]">VyroPortify</span>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="rounded-lg p-1.5 text-[var(--pf-muted)] hover:text-[var(--pf-text)]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex-1 px-3 py-4 space-y-1">
              {NAV.map(({ href, label, icon: Icon }) => {
                const active =
                  href === "/dashboard"
                    ? pathname === href
                    : pathname.startsWith(href);
                return (
                  <Link
                    key={href}
                    href={href}
                    onClick={() => setOpen(false)}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                      active
                        ? "bg-[var(--pf-accent-soft)] text-[var(--pf-accent-text)]"
                        : "text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)]"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                );
              })}
            </nav>
          </aside>
        </div>
      )}
    </>
  );
}
