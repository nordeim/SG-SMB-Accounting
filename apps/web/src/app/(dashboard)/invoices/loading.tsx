import { Skeleton, SkeletonTable, SkeletonCard } from "@/components/ui/skeleton";

/**
 * Invoices Loading State
 *
 * Purpose: Loading placeholder for the invoices list route
 */

export default function InvoicesLoading() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton variant="text" className="w-40 h-8" />
          <Skeleton variant="text" className="w-56 h-4" />
        </div>
        <Skeleton className="w-36 h-10" />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 p-4 border border-border/50 bg-carbon/30">
        <Skeleton className="w-48 h-10" />
        <Skeleton className="w-48 h-10" />
        <Skeleton className="w-32 h-10 ml-auto" />
      </div>

      {/* Invoices table */}
      <SkeletonTable rows={8} columns={6} />

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <Skeleton variant="text" className="w-32 h-4" />
        <div className="flex gap-2">
          <Skeleton className="w-20 h-9" />
          <Skeleton className="w-20 h-9" />
        </div>
      </div>
    </div>
  );
}
