"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import "./globals.css";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    // Log to error reporting service
    console.error("Critical Application Error:", error);
  }, [error]);

  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-void min-h-screen flex items-center justify-center p-4">
        <div className="max-w-md w-full border border-alert bg-carbon p-8 relative overflow-hidden">
          {/* Accent corner */}
          <div className="absolute top-0 right-0 w-16 h-16 bg-alert/10 -translate-y-1/2 translate-x-1/2 rotate-45" />

          {/* Error icon */}
          <div className="mb-6 flex items-center gap-3">
            <div className="p-3 border border-alert bg-alert/10">
              <AlertTriangle className="h-8 w-8 text-alert" />
            </div>
            <span className="font-mono text-xs text-alert uppercase tracking-wider">
              Critical Error
            </span>
          </div>

          {/* Title */}
          <h1 className="font-display text-2xl font-bold text-text-primary mb-3">
            Application Crashed
          </h1>

          {/* Description */}
          <p className="text-text-secondary mb-6 leading-relaxed">
            A critical error occurred that prevented the application from
            loading. Please try refreshing the page.
          </p>

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

          {/* Reset button */}
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-6 py-3 bg-alert text-carbon font-medium
                       hover:bg-alert/90 transition-colors border border-alert"
          >
            <RefreshCw className="h-4 w-4" />
            Reload Application
          </button>

          {/* Support */}
          <p className="mt-6 text-xs text-text-muted">
            If reloading doesn&apos;t help, please contact{" "}
            <a
              href="mailto:support@ledgersg.sg"
              className="text-accent-primary hover:underline"
            >
              support@ledgersg.sg
            </a>
          </p>
        </div>
      </body>
    </html>
  );
}
