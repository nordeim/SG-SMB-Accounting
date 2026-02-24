import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, label, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id || generatedId;

    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-text-secondary"
          >
            {label}
            {props.required && (
              <span className="text-alert ml-1" aria-hidden="true">
                *
              </span>
            )}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          className={cn(
            "flex h-10 w-full rounded-sm border bg-surface px-3 py-2 text-sm",
            "text-text-primary placeholder:text-text-muted",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/50 focus-visible:border-accent-primary",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "transition-colors",
            error
              ? "border-alert focus-visible:ring-alert/50 focus-visible:border-alert"
              : "border-border",
            className
          )}
          ref={ref}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-sm text-alert" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
