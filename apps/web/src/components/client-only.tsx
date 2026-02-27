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

  // Render children immediately on server, no loading fallback
  // This prevents hydration mismatch and layout shift
  if (!mounted && !fallback) {
    return <>{children}</>;
  }

  // If a custom fallback is provided, use it during loading
  if (!mounted && fallback) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
