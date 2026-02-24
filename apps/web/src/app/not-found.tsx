import { FileQuestion, Home, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export const metadata = {
  title: "Page Not Found — LedgerSG",
  description: "The requested page could not be found.",
};

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8 bg-void">
      <div className="max-w-md w-full border border-border bg-carbon p-8 relative overflow-hidden">
        {/* Subtle accent corner */}
        <div className="absolute top-0 right-0 w-16 h-16 bg-accent-primary/5 -translate-y-1/2 translate-x-1/2 rotate-45" />

        {/* 404 Code */}
        <div className="mb-6">
          <span className="font-mono text-6xl font-bold text-text-muted/30">
            404
          </span>
        </div>

        {/* Icon */}
        <div className="mb-6 flex items-center gap-3">
          <div className="p-3 border border-border bg-surface">
            <FileQuestion className="h-8 w-8 text-text-secondary" />
          </div>
          <span className="font-mono text-xs text-text-muted uppercase tracking-wider">
            Not Found
          </span>
        </div>

        {/* Title */}
        <h1 className="font-display text-2xl font-bold text-text-primary mb-3">
          Page Not Found
        </h1>

        {/* Description */}
        <p className="text-text-secondary mb-8 leading-relaxed">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
          Check the URL or navigate back to the dashboard.
        </p>

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <Link href="/dashboard">
            <Button className="gap-2">
              <Home className="h-4 w-4" />
              Go to Dashboard
            </Button>
          </Link>

          <Button
            variant="outline"
            onClick={() => window.history.back()}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Go Back
          </Button>
        </div>

        {/* Help link */}
        <p className="mt-8 text-xs text-text-muted">
          Need help? Contact{" "}
          <a
            href="mailto:support@ledgersg.sg"
            className="text-accent-primary hover:underline"
          >
            support@ledgersg.sg
          </a>
        </p>
      </div>

      {/* Footer */}
      <p className="mt-8 text-xs text-text-muted">
        LedgerSG — IRAS-Compliant Accounting for Singapore SMBs
      </p>
    </div>
  );
}
