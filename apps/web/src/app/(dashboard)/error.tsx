"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/ui/error-fallback";

interface DashboardErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: DashboardErrorProps) {
  useEffect(() => {
    // Log to error reporting service (Sentry-ready)
    console.error("Dashboard Error:", error);
  }, [error]);

  return (
    <ErrorFallback
      error={error}
      reset={reset}
      title="Dashboard Error"
      description="There was a problem loading the dashboard. Please try again."
    />
  );
}
