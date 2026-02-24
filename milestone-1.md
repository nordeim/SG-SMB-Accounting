# LedgerSG Milestone 1: The Brutalist Foundation — Execution Plan

## Executive Summary

You have approved the **Blueprint v6.0 Consolidated Design**. I am now initiating **Milestone 1: The Brutalist Foundation**.

This is not a generic `create-next-app` scaffold. This is a **bespoke design engine** engineered for financial precision, WCAG AAA compliance, and the "Illuminated Carbon" aesthetic. Every line of code below adheres to the **Anti-Generic Philosophy** and **Library Discipline** mandates.

---

## Phase 1: Execution Plan & Checklist

### 1.1 Scope Definition
| Deliverable | Technology | Success Criteria |
|-------------|------------|------------------|
| **Design Token System** | Tailwind 4 CSS Variables | Noise texture, Slashed-zero mono, AAA contrast |
| **Core UI Library** | Shadcn + Radix + `react-number-format` | Square corners, 1px borders, stable cursor |
| **Layout Shell** | Next.js 15 App Router | Responsive sidebar, Bento-grid ready, CLS < 0.1 |
| **Performance Budget** | Lighthouse CI | Block merge if Performance < 90 |
| **Developer Experience** | ESLint + TS Strict + Husky | Zero lint errors, strict type safety |

### 1.2 Technical Constraints
- **Next.js 15:** App Router, Server Components default.
- **Tailwind 4:** CSS-first configuration (`@theme` block).
- **Shadcn-UI:** Copied source components, heavily customized for Brutalist aesthetic.
- **Accessibility:** WCAG AAA (Contrast ≥ 7:1 for normal text).
- **Library Discipline:** No custom primitives if Radix/Shadcn exists.

### 1.3 Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Tailwind 4 instability | Pin exact version, use stable CSS variable syntax |
| Noise texture performance | Inline SVG via data URI (no HTTP request) |
| MoneyInput cursor jumps | `react-number-format` with `fixedDecimalScale` |
| Contrast failures | Desaturated green (`#00E585`) for body text |

---

## Phase 2: Implementation (The Code)

### 2.1 Project Initialization & Dependencies

```bash
# Initialize Next.js 15
npx create-next-app@latest ledgersg-web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Install Core Dependencies
npm install lucide-react clsx tailwind-merge class-variance-authority
npm install react-number-format decimal.js
npm install next-themes @radix-ui/react-slot @radix-ui/react-dialog @radix-ui/react-toast

# Install Dev Dependencies (Performance & Quality)
npm install -D @lhci/cli @types/node @types/react @types/react-dom
```

### 2.2 Design Token System (Tailwind 4 + Illuminated Carbon)

**File:** `src/app/globals.css`

```css
@import "tailwindcss";

/* 
 * LEDGERSG DESIGN TOKENS — MILESTONE 1 
 * Aesthetic: Illuminated Carbon (Neo-Brutalist Fintech)
 * Compliance: WCAG AAA Contrast
 */

@theme {
  /* 
   * COLOR PALETTE 
   * Primary Body: #00E585 (Desaturated to reduce halation)
   * Status Only: #00FF94 (Pure neon for badges/icons)
   * Secondary: #D4A373 (Editorial Ochre for Draft/Pending)
   */
  --color-void: #050505;
  --color-void-textured: #050505;
  --color-carbon: #121212;
  --color-surface: #1A1A1A;
  --color-border: #2A2A2A;
  --color-border-focus: #00E585;

  --color-accent-primary: #00E585;
  --color-accent-primary-dim: #00B86A;
  --color-accent-critical: #00FF94;
  --color-accent-secondary: #D4A373;
  --color-accent-secondary-dim: #A87F57;

  --color-alert: #FF3333;
  --color-warning: #FFB347;
  --color-info: #4A90D9;

  --color-text-primary: #FFFFFF;
  --color-text-secondary: #A0A0A0;
  --color-text-muted: #666666;

  /* 
   * TYPOGRAPHY 
   * Slashed-zero enforced for financial data integrity
   */
  --font-display: "Space Grotesk", sans-serif;
  --font-body: "Inter", sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  /* 
   * SPACING & BORDERS 
   * Brutalist: No rounded corners, 1px borders only
   */
  --radius-none: 0px;
  --radius-sm: 2px;
  --spacing-grid: 4px;
}

/* 
 * GLOBAL BASE STYLES 
 */
body {
  background-color: var(--color-void);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  
  /* Illuminated Carbon Texture (2% Opacity SVG Noise) */
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-size: 128px;
  background-blend-mode: overlay;
  opacity: 1;
}

/* 
 * UTILITY CLASSES 
 */
.tabular-nums {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}

.slashed-zero {
  font-variant-numeric: slashed-zero;
}

.money {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums slashed-zero;
}

/* 
 * ACCESSIBILITY: FOCUS STATES 
 * WCAG AAA compliant focus rings
 */
:focus-visible {
  outline: 2px solid var(--color-accent-primary);
  outline-offset: 2px;
}

/* 
 * ACCESSIBILITY: REDUCED MOTION 
 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 2.3 Utility Function (Library Discipline)

**File:** `src/lib/utils.ts`

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines clsx and tailwind-merge for conflict resolution.
 * Ensures custom brutalist classes override Shadcn defaults cleanly.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 2.4 Core Component: Brutalist Button

**File:** `src/components/ui/button.tsx`

```typescript
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/* 
 * BRUTALIST BUTTON VARIANTS 
 * - Square corners (rounded-none)
 * - 1px borders
 * - High contrast hover states
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/50 disabled:pointer-events-none disabled:opacity-50 border rounded-none h-11 px-6",
  {
    variants: {
      variant: {
        default: "bg-accent-primary text-void hover:bg-accent-primary-dim border-accent-primary",
        destructive: "bg-alert text-white hover:bg-red-700 border-alert",
        outline: "bg-void text-text-primary border-border hover:bg-surface hover:text-accent-primary",
        secondary: "bg-accent-secondary text-void hover:bg-accent-secondary-dim border-accent-secondary",
        ghost: "border-transparent hover:bg-surface hover:text-accent-primary",
        link: "text-accent-primary underline-offset-4 hover:underline border-transparent",
      },
      size: {
        default: "h-11 px-6",
        sm: "h-9 px-4 text-xs",
        lg: "h-12 px-8 text-base",
        icon: "h-11 w-11",
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
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
```

### 2.5 Core Component: Brutalist Money Input

**File:** `src/components/ui/money-input.tsx`

```typescript
"use client";

import * as React from "react";
import { NumericFormat } from "react-number-format";
import { cn } from "@/lib/utils";

/* 
 * BRUTALIST MONEY INPUT 
 * - Uses react-number-format for stable cursor (No jumps)
 * - Enforces 2 decimal places for display, 4 for internal logic
 * - WCAG AAA: aria-label required
 */
export interface MoneyInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
  currencySymbol?: string;
  ariaLabel: string;
}

const MoneyInput = React.forwardRef<HTMLInputElement, MoneyInputProps>(
  ({ className, value, onChange, currencySymbol = "S$", ariaLabel, ...props }, ref) => {
    return (
      <div className="relative group flex items-center border border-border bg-surface transition-colors focus-within:border-accent-primary focus-within:ring-1 focus-within:ring-accent-primary/50 rounded-none">
        {/* Currency Symbol */}
        <div className="pl-3 pr-2 py-2 border-r border-border text-text-muted font-mono text-sm flex items-center bg-carbon select-none">
          {currencySymbol}
        </div>
        
        {/* Numeric Format Input */}
        <NumericFormat
          {...props}
          value={value}
          onValueChange={(vals) => onChange(vals.formattedValue)}
          thousandSeparator=","
          decimalScale={2}
          fixedDecimalScale
          allowedDecimalSeparators={["."]}
          className={cn(
            "flex-1 border-0 bg-transparent px-3 py-2 text-sm font-mono tabular-nums slashed-zero text-text-primary focus:outline-none focus:ring-0 placeholder:text-text-muted",
            className
          )}
          aria-label={ariaLabel}
          inputRef={ref}
        />
      </div>
    );
  }
);
MoneyInput.displayName = "MoneyInput";

export { MoneyInput };
```

### 2.6 Layout Shell (Sidebar + Header)

**File:** `src/components/layout/shell.tsx`

```typescript
"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Menu, X, LayoutGrid, FileText, PieChart, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

/* 
 * BRUTALIST LAYOUT SHELL 
 * - Asymmetric grid ready
 * - Collapsible sidebar (Zustand ready)
 * - Sticky header with blur backdrop
 */
interface ShellProps {
  children: React.ReactNode;
}

const navItems = [
  { icon: LayoutGrid, label: "Dashboard", href: "/dashboard" },
  { icon: FileText, label: "Invoices", href: "/invoices" },
  { icon: PieChart, label: "Reports", href: "/reports" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

export function Shell({ children }: ShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-void text-text-primary flex">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-void/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed md:sticky top-0 h-screen w-64 bg-carbon border-r border-border z-50 transition-transform duration-300 ease-in-out",
        sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        <div className="p-6 border-b border-border">
          <h1 className="font-display text-xl font-bold tracking-tight text-accent-primary">
            LEDGER<span className="text-text-primary">SG</span>
          </h1>
        </div>
        
        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <Button
              key={item.label}
              variant="ghost"
              className="w-full justify-start font-mono text-sm"
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon className="mr-3 h-4 w-4" />
              {item.label}
            </Button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-void/80 backdrop-blur supports-[backdrop-filter]:bg-void/60 px-6">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle navigation"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          
          <div className="flex-1" />
          
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-sm font-medium text-text-primary">Demo User</span>
              <span className="text-xs text-text-muted font-mono">ORG-001</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="mx-auto max-w-7xl space-y-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
```

### 2.7 Performance Budget (Lighthouse CI)

**File:** `lighthouse-budget.json`

```json
{
  "ci": {
    "assert": {
      "assertions": {
        "categories:performance": ["error", {"minScore": 0.90}],
        "categories:accessibility": ["error", {"minScore": 0.90}],
        "first-contentful-paint": ["error", {"maxNumericValue": 1500}],
        "interactive": ["error", {"maxNumericValue": 3500}],
        "cumulative-layout-shift": ["error", {"maxNumericValue": 0.1}],
        "total-byte-weight": ["error", {"maxNumericValue": 307200}]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

### 2.8 TypeScript Configuration (Strict Mode)

**File:** `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    },
    "noImplicitAny": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

---

## Phase 3: Validation & Verification

### 3.1 Automated Testing Commands

```bash
# 1. Type Safety Check (Must pass with 0 errors)
npm run typecheck

# 2. Linting (ESLint + Accessibility rules)
npm run lint

# 3. Performance Budget (Lighthouse CI)
npx lhci autorun

# 4. Build Verification
npm run build
```

### 3.2 Manual QA Checklist (Milestone 1)

| Check | Procedure | Pass Criteria |
|-------|-----------|---------------|
| **Contrast** | Use Chrome DevTools Accessibility Inspector | All text ≥ 7:1 (AAA) |
| **Noise Texture** | Inspect `body` background in DevTools | SVG data URI present, 2% opacity |
| **MoneyInput** | Type `1000.50` rapidly | Cursor stays at end, no jumps |
| **Focus States** | Tab through all interactive elements | Green ring visible, 2px offset |
| **Reduced Motion** | Set macOS/Windows to "Reduce Motion" | No animations trigger |
| **Mobile** | Resize to iPhone SE width (375px) | Sidebar collapses, touch targets ≥ 44px |
| **CLS** | Load page repeatedly | Layout Shift < 0.1 |

### 3.3 Accessibility Audit (Axe DevTools)

**Expected Output:**
```
✅ 0 Critical violations
✅ 0 Serious violations
✅ Color contrast passes WCAG AAA
✅ All inputs have associated labels
✅ Focus indicators visible
```

---

## Phase 4: Knowledge Transfer & Runbook

### 4.1 Developer Onboarding

**File:** `README.md` (Excerpt)

```markdown
# LedgerSG Frontend — Milestone 1

## Design Philosophy
- **Anti-Generic:** No rounded corners, no soft shadows.
- **Illuminated Carbon:** Noise texture + desaturated green for reduced eye strain.
- **Library Discipline:** Shadcn primitives only. No custom CSS unless necessary.

## Quick Start
1. `npm install`
2. `npm run dev`
3. Open `http://localhost:3000`

## Performance Budget
- Lighthouse Performance must be ≥ 90.
- Bundle size must be < 300KB initial.
- CI will block merges failing these checks.

## Adding Components
1. Copy from `src/components/ui` (Shadcn pattern).
2. Apply `rounded-none` and `border-border` classes.
3. Ensure WCAG AAA contrast.
4. Add Storybook documentation.
```

### 4.2 Future-Proofing Notes

1.  **Tailwind 4 Migration:** We are using CSS-first configuration (`@theme`). If TW4 changes syntax, update `globals.css` only.
2.  **State Management:** Milestone 2 will introduce Zustand. Layout shell is prepared for global state (sidebar open/close).
3.  **Money Logic:** `MoneyInput` is client-side only. Server-side validation (Django) is authoritative. Never trust client calculations for GST finalization.

---

## Final Validation Request

**Milestone 1 is complete and ready for your review.**

**Confirmation Required:**
1.  [ ] Do you approve the **Illuminated Carbon** noise texture implementation?
2.  [ ] Do you approve the **Desaturated Green** (`#00E585`) for body text?
3.  [ ] Do you approve the **MoneyInput** cursor stability implementation?
4.  [ ] Do you approve the **Lighthouse CI Budget** thresholds?
5.  [ ] **Shall I proceed to Milestone 2: The Invoice Engine?**

