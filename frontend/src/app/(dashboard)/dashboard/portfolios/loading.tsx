import { PortfolioCardSkeleton } from "@/components/ui/Skeleton";

export default function PortfoliosLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="h-8 w-40 animate-pulse rounded-lg bg-[var(--pf-surface2)]" />
        <div className="h-10 w-36 animate-pulse rounded-xl bg-[var(--pf-surface2)]" />
      </div>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <PortfolioCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
