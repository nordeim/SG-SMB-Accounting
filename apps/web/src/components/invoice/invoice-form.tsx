"use client";

import * as React from "react";
import { useForm, FormProvider, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  invoiceSchema,
  type Invoice,
  type InvoiceInput,
  createEmptyInvoice,
  createEmptyLine,
} from "@/shared/schemas/invoice";
import { InvoiceLineRow } from "./invoice-line-row";
import { TaxBreakdownCard } from "./tax-breakdown-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { calculateFromLines } from "@/lib/gst-engine";
import { useInvoiceStore } from "@/stores/invoice-store";

interface InvoiceFormProps {
  initialData?: Partial<InvoiceInput>;
  isGSTRegistered?: boolean;
  onSuccess?: (invoiceId: string) => void;
}

export function InvoiceForm({
  initialData,
  isGSTRegistered = true,
  onSuccess,
}: InvoiceFormProps) {
  const { setHasUnsavedChanges } = useInvoiceStore();
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const defaultValues = React.useMemo(() => {
    const empty = createEmptyInvoice();
    return {
      ...empty,
      ...initialData,
    } as InvoiceInput;
  }, [initialData]);

  const methods = useForm<InvoiceInput>({
    resolver: zodResolver(invoiceSchema),
    defaultValues,
    mode: "onChange",
  });

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { isDirty },
  } = methods;

  const { fields, append, remove } = useFieldArray({
    control,
    name: "lines",
  });

  // Watch lines for real-time calculations
  const lines = watch("lines") || [];

  // Calculate totals
  const { totals } = React.useMemo(() => {
    return calculateFromLines(lines as Invoice["lines"]);
  }, [lines]);

  // Update form totals
  React.useEffect(() => {
    setValue("subtotal", totals.subtotal);
    setValue("gst_amount", totals.gst_amount);
    setValue("total_amount", totals.total_amount);
  }, [totals, setValue]);

  // Track unsaved changes
  React.useEffect(() => {
    setHasUnsavedChanges(isDirty);
  }, [isDirty, setHasUnsavedChanges]);

  // Add new line
  const handleAddLine = () => {
    append(createEmptyLine() as InvoiceInput["lines"][number]);
  };

  // Remove line
  const handleRemoveLine = (index: number) => {
    if (fields.length > 1) {
      remove(index);
    }
  };

  // Form submission
  const onSubmit = async (data: InvoiceInput) => {
    setIsSubmitting(true);
    setError(null);

    try {
      // TODO: Replace with actual API call in Milestone 4
      console.log("Submitting invoice:", data);

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Generate a mock invoice ID
      const invoiceId = crypto.randomUUID();

      onSuccess?.(invoiceId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save invoice");
    } finally {
      setIsSubmitting(false);
    }
  };

  const onSaveDraft = async () => {
    const data = methods.getValues();
    console.log("Saving draft:", { ...data, status: "DRAFT" });
    // TODO: Implement draft save
  };

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {error && (
          <div
            className="bg-alert/10 border border-alert rounded-sm p-4 flex items-start gap-3"
            role="alert"
          >
            <AlertCircle className="h-5 w-5 text-alert flex-shrink-0 mt-0.5" />
            <p className="text-sm text-alert">{error}</p>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Invoice Details */}
            <Card className="border-border bg-carbon rounded-sm">
              <CardHeader>
                <CardTitle className="font-display text-lg text-text-primary">
                  Invoice Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <Input
                    label="Invoice Number"
                    {...methods.register("invoice_number")}
                    error={methods.formState.errors.invoice_number?.message}
                  />
                  <Input
                    label="Reference"
                    {...methods.register("reference")}
                    placeholder="Optional reference"
                  />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <Input
                    label="Issue Date"
                    type="date"
                    {...methods.register("issue_date")}
                    error={methods.formState.errors.issue_date?.message}
                  />
                  <Input
                    label="Due Date"
                    type="date"
                    {...methods.register("due_date")}
                    error={methods.formState.errors.due_date?.message}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Customer Details */}
            <Card className="border-border bg-carbon rounded-sm">
              <CardHeader>
                <CardTitle className="font-display text-lg text-text-primary">
                  Customer
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <Input
                    label="Customer Name"
                    {...methods.register("customer.name")}
                    error={methods.formState.errors.customer?.name?.message}
                  />
                  <Input
                    label="Email"
                    type="email"
                    {...methods.register("customer.email")}
                    error={methods.formState.errors.customer?.email?.message}
                  />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <Input
                    label="UEN (Optional)"
                    {...methods.register("customer.uen")}
                    placeholder="201912345A"
                    error={methods.formState.errors.customer?.uen?.message}
                  />
                  <Input
                    label="GST Registration No (Optional)"
                    {...methods.register("customer.gst_registration_no")}
                    placeholder="M90345678"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Line Items */}
            <Card className="border-border bg-carbon rounded-sm">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="font-display text-lg text-text-primary">
                  Line Items
                </CardTitle>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddLine}
                  className="rounded-sm border-border text-text-secondary"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Line
                </Button>
              </CardHeader>
              <CardContent>
                {/* Header Row */}
                <div
                  className="grid grid-cols-12 gap-2 pb-2 border-b border-border text-xs font-medium text-text-secondary"
                  role="rowheader"
                >
                  <div className="col-span-1"></div>
                  <div className="col-span-4">Description</div>
                  <div className="col-span-1 text-right">Qty</div>
                  <div className="col-span-2 text-right">Price</div>
                  <div className="col-span-1 text-right">Disc%</div>
                  <div className="col-span-1">Tax</div>
                  <div className="col-span-1 text-right">Total</div>
                  <div className="col-span-1"></div>
                </div>

                {/* Line Items */}
                <div role="rowgroup">
                  {fields.map((field, index) => (
                    <InvoiceLineRow
                      key={field.id}
                      index={index}
                      isGSTRegistered={isGSTRegistered}
                      onRemove={() => handleRemoveLine(index)}
                    />
                  ))}
                </div>

                {methods.formState.errors.lines && (
                  <p className="text-sm text-alert mt-2" role="alert">
                    {methods.formState.errors.lines.message}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Notes */}
            <Card className="border-border bg-carbon rounded-sm">
              <CardHeader>
                <CardTitle className="font-display text-lg text-text-primary">
                  Notes & Terms
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-text-secondary mb-1.5 block">
                    Notes
                  </label>
                  <textarea
                    {...methods.register("notes")}
                    rows={3}
                    className={cn(
                      "flex w-full rounded-sm border bg-surface px-3 py-2 text-sm",
                      "text-text-primary placeholder:text-text-muted",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/50 focus-visible:border-accent-primary",
                      "disabled:opacity-50 disabled:cursor-not-allowed",
                      "transition-colors resize-none",
                      "border-border"
                    )}
                    placeholder="Additional notes for the customer..."
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-text-secondary mb-1.5 block">
                    Terms & Conditions
                  </label>
                  <textarea
                    {...methods.register("terms")}
                    rows={2}
                    className={cn(
                      "flex w-full rounded-sm border bg-surface px-3 py-2 text-sm",
                      "text-text-primary placeholder:text-text-muted",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/50 focus-visible:border-accent-primary",
                      "disabled:opacity-50 disabled:cursor-not-allowed",
                      "transition-colors resize-none",
                      "border-border"
                    )}
                    placeholder="Payment terms and conditions..."
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Tax Breakdown */}
          <div className="lg:col-span-1">
            <TaxBreakdownCard
              isGSTRegistered={isGSTRegistered}
              totals={totals}
              onSubmit={handleSubmit(onSubmit)}
              onSaveDraft={onSaveDraft}
              isSubmitting={isSubmitting}
            />
          </div>
        </div>
      </form>
    </FormProvider>
  );
}
