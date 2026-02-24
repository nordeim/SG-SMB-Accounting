import { Skeleton, SkeletonForm, SkeletonCard } from "@/components/ui/skeleton";

/**
 * Settings Loading State
 *
 * Purpose: Loading placeholder for the settings route
 */

export default function SettingsLoading() {
  return (
    <div className="max-w-3xl space-y-6">
      {/* Page header */}
      <div className="space-y-2">
        <Skeleton variant="text" className="w-32 h-8" />
        <Skeleton variant="text" className="w-56 h-4" />
      </div>

      {/* Settings sections */}
      <SkeletonCard className="p-6">
        <Skeleton variant="text" className="w-40 h-6 mb-2" />
        <Skeleton variant="text" className="w-64 h-4 mb-6" />
        <SkeletonForm fields={4} />
      </SkeletonCard>

      <SkeletonCard className="p-6">
        <Skeleton variant="text" className="w-48 h-6 mb-2" />
        <Skeleton variant="text" className="w-72 h-4 mb-6" />
        <SkeletonForm fields={3} />
      </SkeletonCard>

      <SkeletonCard className="p-6">
        <Skeleton variant="text" className="w-36 h-6 mb-2" />
        <Skeleton variant="text" className="w-64 h-4 mb-6" />
        <SkeletonForm fields={2} />
      </SkeletonCard>

      {/* Save button */}
      <div className="flex justify-end">
        <Skeleton className="w-32 h-10" />
      </div>
    </div>
  );
}
