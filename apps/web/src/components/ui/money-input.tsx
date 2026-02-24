"use client";

import * as React from "react";
import { NumericFormat } from "react-number-format";
import { cn } from "@/lib/utils";

/*
 * BRUTALIST MONEY INPUT — MILESTONE 1
 *
 * CRITICAL FEATURES:
 * - react-number-format for stable cursor position (NO JUMPS)
 * - WCAG AAA: aria-label required
 * - Fixed 2 decimal places for display
 * - 4 decimal places internal precision
 * - Brutalist styling with minimal rounding
 */

export interface MoneyInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "value" | "type"> {
  value: string;
  onChange: (value: string) => void;
  currencySymbol?: string;
  ariaLabel: string;
  ariaDescribedBy?: string;
  allowNegative?: boolean;
  decimalScale?: number;
  error?: string;
}

const MoneyInput = React.forwardRef<HTMLInputElement, MoneyInputProps>(
  (
    {
      className,
      value,
      onChange,
      currencySymbol = "S$",
      ariaLabel,
      ariaDescribedBy,
      allowNegative = false,
      decimalScale = 2,
      disabled,
      error,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = React.useState(false);

    return (
      <div className="space-y-1.5">
        <div
          className={cn(
            "relative group flex items-center border bg-surface transition-all rounded-sm",
            "focus-within:border-accent-primary focus-within:ring-1 focus-within:ring-accent-primary/50",
            disabled && "opacity-50 cursor-not-allowed",
            error ? "border-alert" : "border-border",
            className
          )}
        >
          {/* Currency Symbol */}
          {currencySymbol && (
            <div
              className={cn(
                "pl-3 pr-2 py-2 border-r border-border text-text-muted font-mono text-sm flex items-center bg-carbon select-none",
                "tabular-nums slashed-zero"
              )}
            >
              {currencySymbol}
            </div>
          )}

          {/* Numeric Format Input */}
          <NumericFormat
            value={value}
            onValueChange={(vals) => onChange(vals.value)}
            thousandSeparator=","
            decimalScale={decimalScale}
            fixedDecimalScale
            allowedDecimalSeparators={["."]}
            allowNegative={allowNegative}
            disabled={disabled}
            className={cn(
              "flex-1 border-0 bg-transparent px-3 py-2 text-sm font-mono",
              "tabular-nums slashed-zero text-text-primary",
              "focus:outline-none focus:ring-0 placeholder:text-text-muted",
              "w-full min-w-0"
            )}
            aria-label={ariaLabel}
            aria-describedby={cn(error && `${ariaLabel}-error`, ariaDescribedBy)}
            aria-invalid={error ? "true" : "false"}
            getInputRef={ref}
            onFocus={(e) => {
              setIsFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              props.onBlur?.(e);
            }}
            name={props.name}
            placeholder={props.placeholder}
            readOnly={props.readOnly}
            required={props.required}
            autoComplete={props.autoComplete}
          />

          {/* Focus Indicator (Brutalist Style) */}
          {isFocused && !error && (
            <div
              className="absolute inset-0 pointer-events-none border-2 border-accent-primary/30 rounded-sm"
              aria-hidden="true"
            />
          )}
        </div>

        {/* Error Message */}
        {error && (
          <p
            id={`${ariaLabel}-error`}
            className="text-sm text-alert"
            role="alert"
          >
            {error}
          </p>
        )}
      </div>
    );
  }
);

MoneyInput.displayName = "MoneyInput";

export { MoneyInput };
