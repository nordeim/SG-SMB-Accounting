import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-sm border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-void",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-accent-primary text-void hover:bg-accent-primary-dim",
        secondary:
          "border-transparent bg-accent-secondary text-void hover:bg-accent-secondary-dim",
        destructive:
          "border-transparent bg-alert text-white hover:bg-red-700",
        outline: "text-text-primary border-border hover:bg-surface",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
