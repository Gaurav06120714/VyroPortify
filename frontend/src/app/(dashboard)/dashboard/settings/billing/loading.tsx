import { BillingSkeleton } from "@/components/ui/Skeleton";

export default function BillingLoading() {
  return (
    <div className="max-w-2xl space-y-6">
      <div className="h-8 w-32 animate-pulse rounded-lg bg-[var(--pf-surface2)]" />
      <BillingSkeleton />
    </div>
  );
}
