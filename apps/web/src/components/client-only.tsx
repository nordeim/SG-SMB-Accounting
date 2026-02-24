"use client";

import * as React from "react";
import { SkeletonCard } from "@/components/ui/skeleton";

/**
 * CLIENT ONLY WRAPPER
 *
 * Purpose: Prevents SSR/hydration issues with interactive components
 * Usage: Wrap any component that uses event handlers (onClick, onSubmit, etc.)
 */

interface ClientOnlyProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function ClientOnly({ children, fallback }: ClientOnlyProps) {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      fallback || (
        <div className="min-h-[50vh] flex items-center justify-center">
          <SkeletonCard className="w-full max-w-md p-6" />
        </div>
      )
    );
  }

  return <>{children}</>;
}
