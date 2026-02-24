"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import type { InvoiceTotals } from "@/lib/gst-engine";

interface TaxBreakdownCardProps {
  isGSTRegistered: boolean;
  totals: InvoiceTotals | null;
  onSubmit: () => void;
  onSaveDraft: () => void;
  isSubmitting: boolean;
}

export function TaxBreakdownCard({
  isGSTRegistered,
  totals,
  onSubmit,
  onSaveDraft,
  isSubmitting,
}: TaxBreakdownCardProps) {
  const [announcement, setAnnouncement] = React.useState("");

  // Screen reader announcement when totals change
  React.useEffect(() => {
    if (totals) {
      setAnnouncement(`Invoice total updated to S$ ${totals.display_total}`);
    }
  }, [totals?.display_total]);

  if (!totals) {
    return (
      <Card className="border-border bg-carbon rounded-sm sticky top-20">
        <CardHeader className="pb-3">
          <CardTitle className="font-display text-lg text-text-primary">
            Tax Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-surface rounded-sm" />
            <div className="h-4 bg-surface rounded-sm" />
            <div className="h-4 bg-surface rounded-sm" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border bg-carbon rounded-sm sticky top-20">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="font-display text-lg text-text-primary">
            Tax Breakdown
          </CardTitle>
          {isGSTRegistered && (
            <Badge
              variant="outline"
              className="border-accent-primary text-accent-primary rounded-sm text-xs"
            >
              GST Registered
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Subtotal */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-text-secondary">Subtotal</span>
          <span className="text-sm font-mono tabular-nums text-text-primary">
            S$ {totals.display_subtotal}
          </span>
        </div>

        {/* GST Amount */}
        {isGSTRegistered && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-text-secondary">GST (9%)</span>
            <span className="text-sm font-mono tabular-nums text-accent-primary">
              S$ {totals.display_gst}
            </span>
          </div>
        )}

        {/* Divider */}
        <div className="border-t border-border" />

        {/* Total */}
        <div className="flex justify-between items-center">
          <span className="text-base font-display font-medium text-text-primary">
            Total
          </span>
          <span
            className={cn(
              "text-xl font-mono tabular-nums slashed-zero font-bold",
              "text-accent-primary"
            )}
            aria-live="polite"
            aria-atomic="true"
          >
            S$ {totals.display_total}
          </span>
        </div>

        {/* Screen Reader Announcement (Hidden) */}
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {announcement}
        </div>

        {/* Action Buttons */}
        <div className="pt-4 space-y-2">
          <Button
            type="button"
            variant="outline"
            className="w-full rounded-sm border-border text-text-secondary hover:bg-surface"
            disabled={isSubmitting}
            onClick={onSaveDraft}
          >
            <FileText className="h-4 w-4 mr-2" />
            Save Draft
          </Button>
          <Button
            type="button"
            className="w-full rounded-sm bg-accent-primary text-void hover:bg-accent-primary-dim"
            onClick={onSubmit}
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-void/30 border-t-void rounded-full animate-spin" />
                Processing...
              </span>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Send Invoice
              </>
            )}
          </Button>
        </div>

        {/* Peppol Status Indicator */}
        {isGSTRegistered && (
          <div className="pt-2">
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <div className="w-2 h-2 rounded-full bg-accent-secondary animate-pulse" />
              <span>Peppol Ready</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
