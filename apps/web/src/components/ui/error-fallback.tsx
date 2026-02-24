"use client";

import { AlertTriangle, RefreshCw, Home, ArrowLeft } from "lucide-react";
import { Button } from "./button";

interface ErrorFallbackProps {
  error: Error & { digest?: string };
  reset?: () => void;
  title?: string;
  description?: string;
  showHome?: boolean;
  showBack?: boolean;
}

export function ErrorFallback({
  error,
  reset,
  title = "Something went wrong",
  description = "An unexpected error occurred. We've logged this and will investigate.",
  showHome = true,
  showBack = true,
}: ErrorFallbackProps) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center p-8">
      <div className="max-w-md w-full border border-alert bg-carbon p-8 relative overflow-hidden">
        {/* Accent corner accent */}
        <div className="absolute top-0 right-0 w-16 h-16 bg-alert/10 -translate-y-1/2 translate-x-1/2 rotate-45" />

        {/* Error icon */}
        <div className="mb-6 flex items-center gap-3">
          <div className="p-3 border border-alert bg-alert/10">
            <AlertTriangle className="h-8 w-8 text-alert" />
          </div>
          <span className="font-mono text-xs text-alert uppercase tracking-wider">
            Error
          </span>
        </div>

        {/* Title */}
        <h1 className="font-display text-2xl font-bold text-text-primary mb-3">
          {title}
        </h1>

        {/* Description */}
        <p className="text-text-secondary mb-6 leading-relaxed">{description}</p>

        {/* Error details (dev mode only) */}
        {process.env.NODE_ENV === "development" && (
          <div className="mb-6 p-4 bg-void border border-border overflow-auto">
            <code className="font-mono text-xs text-alert block">
              {error.message}
            </code>
            {error.digest && (
              <span className="font-mono text-xs text-text-muted block mt-2">
                Digest: {error.digest}
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          {reset && (
            <Button
              onClick={reset}
              className="gap-2 bg-alert hover:bg-alert/90"
            >
              <RefreshCw className="h-4 w-4" />
              Try Again
            </Button>
          )}

          {showBack && (
            <Button
              variant="outline"
              onClick={() => window.history.back()}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Go Back
            </Button>
          )}

          {showHome && (
            <Button variant="ghost" onClick={() => (window.location.href = "/")}>
              <Home className="h-4 w-4 mr-2" />
              Home
            </Button>
          )}
        </div>

        {/* Support link */}
        <p className="mt-6 text-xs text-text-muted">
          If this problem persists, please contact{" "}
          <a
            href="mailto:support@ledgersg.sg"
            className="text-accent-primary hover:underline"
          >
            support@ledgersg.sg
          </a>
        </p>
      </div>
    </div>
  );
}
