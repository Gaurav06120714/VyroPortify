"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  User,
  Bell,
  CreditCard,
  Key,
  Palette,
  AlertTriangle,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  danger?: boolean;
}

const ITEMS: NavItem[] = [
  { href: "/dashboard/settings", label: "Profile", icon: User },
  { href: "/dashboard/settings/billing", label: "Billing", icon: CreditCard },
  { href: "/dashboard/settings/notifications", label: "Notifications", icon: Bell },
  { href: "/dashboard/settings/appearance", label: "Appearance", icon: Palette },
  { href: "/dashboard/settings/api", label: "API", icon: Key },
  { href: "/dashboard/settings/danger", label: "Danger Zone", icon: AlertTriangle, danger: true },
];

export function SettingsNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Settings sections" className="space-y-1">
      {ITEMS.map(({ href, label, icon: Icon, danger }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              active
                ? "bg-[var(--pf-accent-subtle)] text-[var(--pf-text)] font-medium"
                : danger
                ? "text-red-500 hover:bg-red-500/5"
                : "text-[var(--pf-text-dim)] hover:bg-[var(--pf-surface2)]",
            )}
          >
            <Icon className="h-4 w-4" aria-hidden />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
