"use client";

import { Metadata } from "next";
import { useRouter } from "next/navigation";
import { InvoiceForm } from "@/components/invoice/invoice-form";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NewInvoicePage() {
  const router = useRouter();

  const handleSuccess = (invoiceId: string) => {
    // Redirect to invoice detail page after successful creation
    router.push(`/invoices/${invoiceId}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/invoices">
          <Button
            variant="outline"
            size="icon"
            className="rounded-sm border-border text-text-secondary"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            New Invoice
          </h1>
          <p className="text-sm text-text-secondary">
            Create a new sales invoice
          </p>
        </div>
      </div>

      {/* Invoice Form */}
      <InvoiceForm
        isGSTRegistered={true}
        onSuccess={handleSuccess}
      />
    </div>
  );
}
