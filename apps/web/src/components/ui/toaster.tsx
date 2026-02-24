"use client";

import { useToast } from "@/hooks/use-toast";
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
  ToastIcon,
} from "@/components/ui/toast";

/**
 * LEDGERSG TOASTER
 *
 * Purpose: Toast container component that renders all active toasts
 * Usage: Mount once in root layout
 */

export function Toaster() {
  const { toasts } = useToast();

  return (
    <ToastProvider swipeDirection="right">
      {toasts.map(function ({
        id,
        title,
        description,
        action,
        variant = "default",
        ...props
      }) {
        const Icon = ToastIcon[variant];

        return (
          <Toast key={id} variant={variant} {...props}>
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div
                className={`
                mt-0.5 shrink-0
                ${variant === "success" ? "text-accent-primary" : ""}
                ${variant === "error" ? "text-alert" : ""}
                ${variant === "warning" ? "text-accent-secondary" : ""}
                ${variant === "default" || variant === "info" ? "text-text-muted" : ""}
              `}
              >
                <Icon className="h-5 w-5" />
              </div>

              {/* Content */}
              <div className="grid gap-1 flex-1">
                {title && <ToastTitle>{title}</ToastTitle>}
                {description && (
                  <ToastDescription>{description}</ToastDescription>
                )}
              </div>
            </div>

            {/* Action */}
            {action}

            {/* Close button */}
            <ToastClose />
          </Toast>
        );
      })}
      <ToastViewport />
    </ToastProvider>
  );
}
