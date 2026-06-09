"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser, useClerk } from "@clerk/nextjs";
import {
  LayoutDashboard,
  Upload,
  FolderOpen,
  Palette,
  Settings,
  Zap,
  PenLine,
  CreditCard,
  FileText,
  LogOut,
  ChevronDown,
} from "lucide-react";
import { useState } from "react";
import { usePlan } from "@/context/PlanContext";
import ThemeToggle from "@/components/ThemeToggle";

const NAV_TOP = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/build-resume", label: "AI Resume Builder", icon: PenLine },
  { href: "/dashboard/upload", label: "Upload Resume", icon: Upload },
  { href: "/dashboard/portfolios", label: "My Portfolios", icon: FolderOpen },
  { href: "/dashboard/templates", label: "Templates", icon: Palette },
  { href: "/dashboard/cover-letter", label: "Cover Letter", icon: FileText },
];

const NAV_BOTTOM = [
  { href: "/dashboard/settings/billing", label: "Billing", icon: CreditCard },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

function UserAvatar({ name, email }: { name: string; email?: string }) {
  const initials = name
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase() || "U";

  const { signOut } = useClerk();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 rounded-lg p-2 transition-colors hover:bg-[var(--pf-border-subtle)]"
      >
        {}
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--pf-accent)] to-[#8b5cf6] text-sm font-bold text-white shadow-sm">
          {initials}
        </div>
        <div className="min-w-0 flex-1 text-left">
          <p className="truncate text-sm font-medium text-[var(--pf-text)]">{name}</p>
          {email && (
            <p className="truncate text-xs text-[var(--pf-muted)]">{email}</p>
          )}
        </div>
        <ChevronDown
          className={`h-3.5 w-3.5 flex-shrink-0 text-[var(--pf-muted)] transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full left-0 right-0 z-50 mb-1 overflow-hidden rounded-xl border border-[var(--pf-border)] bg-[var(--pf-surface)] shadow-xl">
            <Link
              href="/dashboard/settings"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)] transition-colors"
            >
              <Settings className="h-4 w-4" />
              Account Settings
            </Link>
            <div className="h-px bg-[var(--pf-border-dim)]" />
            <button
              onClick={() => signOut({ redirectUrl: "/" })}
              className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useUser();
  const { plan } = usePlan();

  const displayName =
    [user?.firstName, user?.lastName].filter(Boolean).join(" ") ||
    user?.username ||
    "User";

  const navLink = (href: string, label: string, Icon: React.ElementType) => {
    const active = href === "/dashboard" ? pathname === href : pathname.startsWith(href);
    return (
      <Link
        key={href}
        href={href}
        className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
          active
            ? "bg-[var(--pf-accent-soft)] text-[var(--pf-accent-text)]"
            : "text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)]"
        }`}
      >
        <Icon className="h-4 w-4 flex-shrink-0" />
        {label}
      </Link>
    );
  };

  return (
    <aside className="flex h-full w-64 flex-col border-r border-[var(--pf-border-dim)] bg-[var(--pf-bg)]">
      {}
      <Link
        href="/"
        className="flex h-16 items-center gap-2.5 border-b border-[var(--pf-border-dim)] px-6 transition-opacity hover:opacity-80"
      >
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--pf-accent)]">
          <Zap className="h-4 w-4 text-white" />
        </div>
        <span className="text-lg font-bold text-[var(--pf-text)]">VyroPortify</span>
      </Link>

      {}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {NAV_TOP.map(({ href, label, icon: Icon }) => navLink(href, label, Icon))}

        <div className="my-3 h-px bg-[var(--pf-border-dim)]" />

        {NAV_BOTTOM.map(({ href, label, icon: Icon }) => navLink(href, label, Icon))}

        {}
        {plan === "free" && (
          <Link
            href="/pricing"
            className="mt-2 flex items-center gap-2 rounded-lg border border-[var(--pf-border-medium)] bg-[var(--pf-border-faint)] px-3 py-2.5 text-xs font-semibold text-[var(--pf-accent-text)] transition-colors hover:bg-[var(--pf-accent-subtle)]"
          >
            <Zap className="h-3.5 w-3.5" />
            Upgrade to Pro — $9/mo
          </Link>
        )}
      </nav>

      {}
      <div className="border-t border-[var(--pf-border-dim)] px-4 py-3 flex items-center justify-between">
        <span className="text-xs font-medium text-[var(--pf-muted)]">Theme</span>
        <ThemeToggle compact />
      </div>

      {}
      <div className="border-t border-[var(--pf-border-dim)] p-3">
        <UserAvatar
          name={displayName}
          email={user?.primaryEmailAddress?.emailAddress}
        />
      </div>
    </aside>
  );
}
