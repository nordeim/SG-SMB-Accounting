import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/*
 * BRUTALIST BUTTON VARIANTS
 * - Minimal rounded corners (rounded-sm for accessibility)
 * - 1px borders
 * - High contrast hover states
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-colors " +
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-void " +
    "focus-visible:ring-accent-primary disabled:pointer-events-none disabled:opacity-50 border",
  {
    variants: {
      variant: {
        default:
          "bg-accent-primary text-void hover:bg-accent-primary-dim border-accent-primary rounded-sm",
        destructive:
          "bg-alert text-white hover:bg-red-700 border-alert rounded-sm",
        outline:
          "bg-void text-text-primary border-border hover:bg-surface hover:text-accent-primary hover:border-accent-primary rounded-sm",
        secondary:
          "bg-accent-secondary text-void hover:bg-accent-secondary-dim border-accent-secondary rounded-sm",
        ghost:
          "border-transparent hover:bg-surface hover:text-accent-primary rounded-sm",
        link:
          "text-accent-primary underline-offset-4 hover:underline border-transparent rounded-sm",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { className, variant, size, asChild = false, loading = false, children, disabled, ...props },
    ref
  ) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading && (
          <span
            className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin"
            aria-hidden="true"
          />
        )}
        {children}
      </Comp>
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };
