"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PenLine,
  FolderOpen,
  Store,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

// v2.2.2 — Bottom tab nav for mobile. Mounted by the dashboard layout
// under lg. Mirrors the desktop sidebar's top-level destinations so the
// mental model carries over.
//
// Five slots is the iOS HIG cap that still leaves room for thumbs;
// secondary destinations (Analytics, Upload, Templates, etc.) reach
// from the dashboard pages themselves.

interface Tab {
  href: string;
  label: string;
  icon: LucideIcon;
  // matchPrefix means "this tab is active for any path that starts with href".
  matchPrefix?: boolean;
}

const TABS: Tab[] = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/dashboard/builder/new", label: "Build", icon: PenLine, matchPrefix: false },
  { href: "/dashboard/portfolios", label: "Portfolios", icon: FolderOpen, matchPrefix: true },
  { href: "/dashboard/marketplace", label: "Market", icon: Store, matchPrefix: true },
  { href: "/dashboard/settings", label: "Settings", icon: Settings, matchPrefix: true },
];

export function BottomTabNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      // env(safe-area-inset-bottom) keeps the bar above iPhone home indicators.
      className="fixed inset-x-0 bottom-0 z-[var(--pf-z-sticky)] flex border-t border-[var(--pf-border-light)] bg-[var(--pf-surface)] lg:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      {TABS.map(({ href, label, icon: Icon, matchPrefix }) => {
        const active = matchPrefix
          ? pathname === href || pathname.startsWith(href + "/")
          : pathname === href;
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex flex-1 flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-medium transition-colors",
              active
                ? "text-[var(--pf-accent)]"
                : "text-[var(--pf-muted)] hover:text-[var(--pf-text)]",
            )}
          >
            <Icon className="h-5 w-5" aria-hidden />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
