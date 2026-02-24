"use client";

import dynamic from "next/dynamic";
import { SkeletonCard, SkeletonForm } from "@/components/ui/skeleton";
import type { InvoiceInput } from "@/shared/schemas/invoice";

// Dynamically import InvoiceForm to avoid SSR issues
const InvoiceForm = dynamic(
  () => import("./invoice-form").then((mod) => mod.InvoiceForm),
  {
    ssr: false,
    loading: () => (
      <SkeletonCard className="p-6">
        <SkeletonForm fields={6} />
      </SkeletonCard>
    ),
  }
);

interface InvoiceFormWrapperProps {
  initialData?: Partial<InvoiceInput>;
  isGSTRegistered?: boolean;
  onSuccess?: (invoiceId: string) => void;
}

export function InvoiceFormWrapper({
  initialData,
  isGSTRegistered = true,
  onSuccess,
}: InvoiceFormWrapperProps) {
  return (
    <InvoiceForm
      initialData={initialData}
      isGSTRegistered={isGSTRegistered}
      onSuccess={onSuccess}
    />
  );
}
