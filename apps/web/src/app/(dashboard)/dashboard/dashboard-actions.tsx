"use client";

import { Button } from "@/components/ui/button";
import { RefreshCw, Receipt } from "lucide-react";
import Link from "next/link";

export function DashboardActions() {
  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        className="rounded-sm border-border text-text-secondary"
        onClick={() => window.location.reload()}
      >
        <RefreshCw className="h-4 w-4 mr-2" />
        Refresh
      </Button>
      <Link href="/invoices/new">
        <Button className="rounded-sm bg-accent-primary text-void hover:bg-accent-primary-dim">
          <Receipt className="h-4 w-4 mr-2" />
          New Invoice
        </Button>
      </Link>
    </div>
  );
}
