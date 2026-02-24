import { Skeleton, SkeletonTable } from "@/components/ui/skeleton";

/**
 * Ledger Loading State
 *
 * Purpose: Loading placeholder for the ledger route
 */

export default function LedgerLoading() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton variant="text" className="w-48 h-8" />
          <Skeleton variant="text" className="w-64 h-4" />
        </div>
        <Skeleton className="w-32 h-10" />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 p-4 border border-border/50 bg-carbon/30">
        <Skeleton className="w-40 h-10" />
        <Skeleton className="w-40 h-10" />
        <Skeleton className="w-40 h-10" />
        <Skeleton className="w-32 h-10 ml-auto" />
      </div>

      {/* Ledger table */}
      <SkeletonTable rows={10} columns={7} />

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <Skeleton variant="text" className="w-40 h-4" />
        <div className="flex gap-2">
          <Skeleton className="w-24 h-9" />
          <Skeleton className="w-24 h-9" />
        </div>
      </div>
    </div>
  );
}
