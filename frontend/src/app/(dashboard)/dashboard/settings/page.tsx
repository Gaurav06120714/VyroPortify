"use client";

import Link from "next/link";
import { useUser, useClerk } from "@clerk/nextjs";
import { LogOut, Trash2, User, CreditCard, ArrowRight } from "lucide-react";
import { usePlan } from "@/context/PlanContext";

export default function SettingsPage() {
  const { user } = useUser();
  const { signOut } = useClerk();
  const { plan } = usePlan();

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[var(--pf-text)]">Settings</h1>
        <p className="mt-1 text-[var(--pf-muted)]">Manage your account and preferences.</p>
      </div>

      {}
      <Section title="Profile">
        <div className="flex items-center gap-4">
          {user?.imageUrl ? (
            
            <img
              src={user.imageUrl}
              alt="Avatar"
              className="h-14 w-14 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--pf-border-light)]">
              <User className="h-6 w-6 text-[var(--pf-accent)]" />
            </div>
          )}
          <div>
            <p className="font-semibold text-[var(--pf-text)]">
              {user?.fullName ?? user?.username ?? "—"}
            </p>
            <p className="text-sm text-[var(--pf-muted)]">
              {user?.primaryEmailAddress?.emailAddress}
            </p>
          </div>
        </div>
        <p className="mt-4 text-sm text-[var(--pf-muted)]">
          Profile details are managed through your Clerk account. To update your name
          or avatar, click the user button in the sidebar.
        </p>
      </Section>

      {}
      <Section title="Plan &amp; Billing">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CreditCard className="h-5 w-5 text-[var(--pf-muted)]" />
            <div>
              <p className="font-semibold capitalize text-[var(--pf-text)]">{plan} Plan</p>
              <p className="text-sm text-[var(--pf-muted)]">
                {plan === "pro" ? "$9/month · All features unlocked" : "Free forever · 3 portfolios"}
              </p>
            </div>
          </div>
          <Link
            href="/dashboard/settings/billing"
            className="flex items-center gap-1.5 rounded-lg border border-[var(--pf-border-light)] px-3 py-2 text-sm text-[var(--pf-muted)] hover:border-[rgba(108,99,255,0.5)] hover:text-[var(--pf-text)] transition-colors"
          >
            {plan === "pro" ? "Manage" : "Upgrade"}
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </Section>

      {}
      <Section title="Danger Zone">
        <div className="space-y-3">
          <DangerAction
            icon={<LogOut className="h-4 w-4" />}
            label="Sign out"
            description="Sign out of your account on this device."
            buttonLabel="Sign out"
            onClick={() => signOut({ redirectUrl: "/" })}
          />
          <DangerAction
            icon={<Trash2 className="h-4 w-4" />}
            label="Delete account"
            description="Permanently delete your account and all data. This cannot be undone."
            buttonLabel="Delete account"
            danger
            onClick={() => alert("Please contact support to delete your account.")}
          />
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-5 space-y-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--pf-muted)]">{title}</h2>
      {children}
    </div>
  );
}

function DangerAction({
  icon,
  label,
  description,
  buttonLabel,
  onClick,
  danger = false,
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  buttonLabel: string;
  onClick: () => void;
  danger?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-[var(--pf-border-dim)] bg-[var(--pf-bg)] p-4">
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 ${danger ? "text-red-400" : "text-[var(--pf-muted)]"}`}>{icon}</div>
        <div>
          <p className="text-sm font-medium text-[var(--pf-text)]">{label}</p>
          <p className="text-xs text-[var(--pf-muted)]">{description}</p>
        </div>
      </div>
      <button
        onClick={onClick}
        className={`flex-shrink-0 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
          danger
            ? "border-red-500/30 text-red-400 hover:bg-red-500/10"
            : "border-[var(--pf-border-light)] text-[var(--pf-muted)] hover:text-[var(--pf-text)]"
        }`}
      >
        {buttonLabel}
      </button>
    </div>
  );
}
