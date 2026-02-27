import { Skeleton, SkeletonStat, SkeletonCard } from "@/components/ui/skeleton";

/**
 * Dashboard Loading State
 *
 * Purpose: Loading placeholder for the dashboard route
 * Design: Matches dashboard layout with skeleton stats and charts
 */

export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton variant="text" className="w-48 h-8" />
          <Skeleton variant="text" className="w-64 h-4" />
        </div>
        <Skeleton className="w-32 h-10" />
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SkeletonStat />
        <SkeletonStat />
        <SkeletonStat />
        <SkeletonStat />
      </div>

      {/* Charts and tables */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SkeletonCard className="min-h-[300px]" />
        <SkeletonCard className="min-h-[300px]" />
      </div>

      {/* Recent activity */}
      <div className="space-y-4">
        <Skeleton variant="text" className="w-32 h-6" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  );
}
