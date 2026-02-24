"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/ui/error-fallback";

interface RootErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function RootError({ error, reset }: RootErrorProps) {
  useEffect(() => {
    // Log to error reporting service (Sentry-ready)
    console.error("Application Error:", error);
  }, [error]);

  return (
    <ErrorFallback
      error={error}
      reset={reset}
      title="Application Error"
      description="Something went wrong loading the application. Please try again or contact support if the problem persists."
    />
  );
}
