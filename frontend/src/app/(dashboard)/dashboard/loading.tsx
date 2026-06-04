import { StatCardSkeleton } from "@/components/ui/Skeleton";

export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="h-8 w-56 animate-pulse rounded-lg bg-[var(--pf-surface2)]" />
        <div className="h-4 w-80 animate-pulse rounded bg-[var(--pf-surface2)]" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[1, 2, 3].map((i) => <StatCardSkeleton key={i} />)}
      </div>

      {/* Quick actions */}
      <div className="space-y-3">
        <div className="h-5 w-32 animate-pulse rounded bg-[var(--pf-surface2)]" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-2xl bg-[var(--pf-surface)]" />
          ))}
        </div>
      </div>

      {/* Recent portfolios */}
      <div className="space-y-3">
        <div className="h-5 w-40 animate-pulse rounded bg-[var(--pf-surface2)]" />
        {[1, 2].map((i) => (
          <div key={i} className="h-16 animate-pulse rounded-xl bg-[var(--pf-surface)]" />
        ))}
      </div>
    </div>
  );
}
