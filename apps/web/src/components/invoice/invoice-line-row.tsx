"use client";

import * as React from "react";
import { useFormContext } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { MoneyInput } from "@/components/ui/money-input";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Trash2, GripVertical } from "lucide-react";
import {
  TAX_CODES,
  TAX_CODE_DESCRIPTIONS,
  type InvoiceLine,
} from "@/shared/schemas/invoice";
import { calculateLineGST } from "@/lib/gst-engine";
import { cn } from "@/lib/utils";

interface InvoiceLineRowProps {
  index: number;
  isGSTRegistered: boolean;
  onRemove: () => void;
}

export function InvoiceLineRow({
  index,
  isGSTRegistered,
  onRemove,
}: InvoiceLineRowProps) {
  const { register, watch, setValue } = useFormContext();

  // Watch line values for real-time calculation
  const line = watch(`lines.${index}`) as InvoiceLine;

  // Calculate GST in real-time (memoized)
  const computed = React.useMemo(() => {
    if (!line) {
      return {
        display_total: "0.00",
        line_subtotal: "0.0000",
        gst_amount: "0.0000",
        line_total: "0.0000",
      };
    }
    return calculateLineGST(
      line.quantity,
      line.unit_price,
      line.discount_pct,
      line.tax_code,
      line.is_bcrs_deposit
    );
  }, [
    line?.quantity,
    line?.unit_price,
    line?.discount_pct,
    line?.tax_code,
    line?.is_bcrs_deposit,
  ]);

  // Update computed values in form (for submission)
  React.useEffect(() => {
    setValue(`lines.${index}.line_subtotal`, computed.line_subtotal);
    setValue(`lines.${index}.gst_amount`, computed.gst_amount);
    setValue(`lines.${index}.line_total`, computed.line_total);
  }, [computed, index, setValue]);

  if (!line) return null;

  return (
    <div
      className={cn(
        "grid gap-2 items-start py-3 border-b border-border last:border-0",
        "grid-cols-12"
      )}
      role="row"
      aria-label={`Invoice line ${index + 1}`}
    >
      {/* Drag Handle */}
      <div className="col-span-1 flex items-center justify-center pt-2">
        <GripVertical className="w-4 h-4 text-text-muted cursor-grab" />
      </div>

      {/* Description */}
      <div className="col-span-4">
        <Input
          {...register(`lines.${index}.description`)}
          placeholder="Item description"
          className={cn(
            "h-10 text-sm border-border bg-surface",
            "focus-visible:ring-accent-primary/50 rounded-sm"
          )}
          aria-label="Line description"
        />
      </div>

      {/* Quantity */}
      <div className="col-span-1">
        <Input
          type="text"
          inputMode="decimal"
          {...register(`lines.${index}.quantity`)}
          className={cn(
            "h-10 text-sm text-right font-mono border-border bg-surface",
            "focus-visible:ring-accent-primary/50 rounded-sm tabular-nums slashed-zero"
          )}
          aria-label="Quantity"
        />
      </div>

      {/* Unit Price */}
      <div className="col-span-2">
        <MoneyInput
          value={line.unit_price}
          onChange={(val) => setValue(`lines.${index}.unit_price`, val)}
          currencySymbol=""
          ariaLabel="Unit price"
          className={cn("h-10 font-mono rounded-sm", "focus-visible:ring-accent-primary/50")}
          decimalScale={4}
        />
      </div>

      {/* Discount % */}
      <div className="col-span-1">
        <Input
          type="text"
          inputMode="decimal"
          {...register(`lines.${index}.discount_pct`)}
          className={cn(
            "h-10 text-sm text-right font-mono border-border bg-surface",
            "focus-visible:ring-accent-primary/50 rounded-sm tabular-nums"
          )}
          aria-label="Discount percentage"
          placeholder="0"
        />
      </div>

      {/* Tax Code */}
      <div className="col-span-1">
        <Select
          value={line.tax_code}
          onValueChange={(val) =>
            setValue(`lines.${index}.tax_code`, val as typeof TAX_CODES[number])
          }
          disabled={!isGSTRegistered}
        >
          <SelectTrigger
            className={cn(
              "h-10 text-xs border-border bg-surface rounded-sm",
              "focus-visible:ring-accent-primary/50"
            )}
            aria-label="Tax code"
          >
            <SelectValue placeholder="Tax" />
          </SelectTrigger>
          <SelectContent>
            {TAX_CODES.map((code) => (
              <SelectItem key={code} value={code} className="text-xs font-mono">
                {code}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Line Total (Read-only, computed) */}
      <div
        className={cn(
          "col-span-1 text-right text-sm font-mono font-medium pt-2",
          "tabular-nums slashed-zero text-text-primary"
        )}
        aria-label="Line total"
        aria-live="polite"
      >
        {computed.display_total}
      </div>

      {/* Remove Button */}
      <div className="col-span-1 flex justify-end pt-1">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onRemove}
          className={cn(
            "h-8 w-8 text-text-muted hover:text-alert",
            "transition-colors rounded-sm"
          )}
          aria-label={`Remove line ${index + 1}`}
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
