import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  variant?: "default" | "card" | "text" | "circle";
}

/**
 * LEDGERSG SKELETON COMPONENT
 *
 * Purpose: Loading placeholder matching "Illuminated Carbon" design system
 * Features: Animated pulse with subtle accent-primary glow
 *
 * Design Notes:
 * - Square corners (rounded-none) per design system
 * - Dark theme appropriate (bg-carbon/50)
 * - Accent glow on pulse animation
 */

export function Skeleton({
  className,
  variant = "default",
}: SkeletonProps) {
  const variantClasses = {
    default: "bg-carbon/50",
    card: "bg-carbon/50 border border-border/50",
    text: "bg-text-muted/20 h-4",
    circle: "bg-carbon/50 rounded-full",
  };

  return (
    <div
      className={cn(
        "animate-pulse",
        variantClasses[variant],
        className
      )}
      style={{
        // Subtle accent-primary glow on pulse
        boxShadow: "0 0 20px rgba(0, 229, 133, 0.05)",
      }}
    />
  );
}

/**
 * Skeleton Card - Full card placeholder
 */
export function SkeletonCard({
  className,
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) {
  if (children) {
    return (
      <div
        className={cn(
          "border border-border/50 bg-carbon/30",
          className
        )}
      >
        {children}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "border border-border/50 bg-carbon/30 p-6 space-y-4",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <Skeleton variant="text" className="w-1/3 h-6" />
        <Skeleton variant="circle" className="w-8 h-8" />
      </div>

      {/* Content */}
      <Skeleton variant="text" className="w-full" />
      <Skeleton variant="text" className="w-5/6" />
      <Skeleton variant="text" className="w-4/6" />

      {/* Footer */}
      <div className="pt-4 flex gap-2">
        <Skeleton className="w-20 h-9" />
        <Skeleton className="w-20 h-9" />
      </div>
    </div>
  );
}

/**
 * Skeleton Stat - Metric card placeholder
 */
export function SkeletonStat({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "border border-border/50 bg-carbon/30 p-6",
        className
      )}
    >
      {/* Label */}
      <Skeleton variant="text" className="w-24 h-4 mb-2" />

      {/* Value */}
      <Skeleton variant="text" className="w-32 h-10 mb-2" />

      {/* Change indicator */}
      <Skeleton variant="text" className="w-16 h-3" />
    </div>
  );
}

/**
 * Skeleton Table - Table placeholder
 */
export function SkeletonTable({
  rows = 5,
  columns = 4,
  className,
}: {
  rows?: number;
  columns?: number;
  className?: string;
}) {
  return (
    <div className={cn("border border-border/50", className)}>
      {/* Header */}
      <div className="bg-carbon/50 p-4 border-b border-border/50">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton
              key={`header-${i}`}
              variant="text"
              className="flex-1 h-5"
            />
          ))}
        </div>
      </div>

      {/* Rows */}
      <div className="divide-y divide-border/50">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={`row-${rowIndex}`} className="p-4 flex gap-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton
                key={`cell-${rowIndex}-${colIndex}`}
                variant="text"
                className="flex-1"
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Skeleton Form - Form placeholder
 */
export function SkeletonForm({
  fields = 4,
  className,
}: {
  fields?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-6", className)}>
      {Array.from({ length: fields }).map((_, i) => (
        <div key={`field-${i}`} className="space-y-2">
          {/* Label */}
          <Skeleton variant="text" className="w-24 h-4" />
          {/* Input */}
          <Skeleton className="w-full h-10" />
        </div>
      ))}

      {/* Submit button */}
      <Skeleton className="w-32 h-10" />
    </div>
  );
}

/**
 * Skeleton List - List items placeholder
 */
export function SkeletonList({
  items = 5,
  className,
}: {
  items?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div
          key={`item-${i}`}
          className="flex items-center gap-4 p-4 border border-border/50 bg-carbon/30"
        >
          <Skeleton variant="circle" className="w-10 h-10" />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" className="w-1/3 h-4" />
            <Skeleton variant="text" className="w-1/2 h-3" />
          </div>
          <Skeleton className="w-20 h-8" />
        </div>
      ))}
    </div>
  );
}
