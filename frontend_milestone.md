• Summary: Milestones 1-3 Complete ✅

I have successfully implemented the LedgerSG Frontend Web Application with the following milestones:

---
Milestone 1: The Brutalist Foundation ✅

Design System:

• Illuminated Carbon aesthetic with dark-first, high-contrast design
• Tailwind CSS v4 with CSS-first configuration (@theme block)
• Custom color palette: Void (#050505), Carbon (#121212), Accent Primary (#00E585)
• Typography: Space Grotesk (display), Inter (body), JetBrains Mono (financial data)
• WCAG AAA compliant with 7:1 contrast ratios

Core Components:

• Button - Brutalist styled with square corners, 1px borders
• Input - Form inputs with proper focus states
• MoneyInput - Financial input with react-number-format for stable cursor
• Card, Badge, Alert, Select - Shadcn/Radix-based components
• Shell - Layout with collapsible sidebar and sticky header

---
Milestone 2: The Invoice Engine ✅

Invoice System:

• Zod Schema - Type-safe validation with IRAS compliance
• GST Calculation Engine - Decimal.js for precise financial calculations
• Tax Codes - SR, ZR, ES, OS, TX, BL, RS with proper GST rates
• BCRS Support - GST-exempt deposit handling

Components:

• InvoiceForm - Complete invoice creation with React Hook Form
• InvoiceLineRow - Dynamic line items with real-time GST calculation
• TaxBreakdownCard - Live totals with screen reader announcements
• InvoiceLine supports: quantity, unit price, discount %, tax code

---
Milestone 3: Data Visualization & Reports ✅

Dashboard Enhancements:

• GST F5 Chart - Recharts bar chart with accessible data table fallback
• Compliance Alerts - Visual alerts for GST filing deadlines
• GST Threshold Monitor - Progress bar showing S$1M threshold
• Financial Cards - GST Payable, Receivables, Cash, Revenue

General Ledger:

• TanStack Table - Sortable, filterable journal entry table
• Column sorting, global search, proper number formatting
• Mock double-entry data (debit/credit pairs)

---
Project Structure:

apps/web/
├── src/
│   ├── app/
│   │   ├── (auth)/login/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── dashboard/page.tsx (enhanced with charts)
│   │   │   ├── invoices/page.tsx + new/page.tsx
│   │   │   ├── ledger/page.tsx (with TanStack Table)
│   │   │   ├── quotes/page.tsx
│   │   │   ├── reports/page.tsx
│   │   │   ├── settings/page.tsx
│   │   │   └── layout.tsx (Shell wrapper)
│   │   ├── layout.tsx (root with fonts)
│   │   └── page.tsx (redirects to dashboard)
│   ├── components/
│   │   ├── ui/ (Button, Input, Card, Badge, Alert, Select, MoneyInput)
│   │   ├── layout/ (Shell with sidebar)
│   │   ├── invoice/ (InvoiceForm, InvoiceLineRow, TaxBreakdownCard)
│   │   ├── dashboard/ (GSTF5Chart)
│   │   └── ledger/ (LedgerTable)
│   ├── lib/
│   │   ├── utils.ts (cn, formatters)
│   │   └── gst-engine.ts (Decimal.js calculations)
│   ├── stores/
│   │   └── invoice-store.ts (Zustand UI state)
│   └── shared/schemas/
│       ├── invoice.ts (Zod schemas)
│       └── dashboard.ts (Dashboard types)
├── dist/ (3.2MB static export)
└── 29 TypeScript files total

---
Build Output:

• 12 static pages generated
• 3.2MB total build size
• Zero TypeScript errors
• Next.js 16 with App Router
• Tailwind CSS v4 with CSS-first theming

---
Routes Implemented:

 Route           Description
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 /               Redirects to dashboard
 /login          Authentication page
 /dashboard      Command Center with GST F5 chart
 /invoices       Invoice list with mock data
 /invoices/new   New invoice form
 /quotes         Quotes management
 /ledger         General ledger with TanStack Table
 /reports        Reports hub
 /settings       Organization & user settings

---
Milestones 4 & 5 (Integration & Final Delivery) would involve:

• API client with TanStack Query
• Django backend integration
• Authentication flow with CSRF
• E2E testing with Playwright
• Production deployment configuration

---

 ✅ Milestone 4 Complete - API Integration Layer

  Files Created:

  1. src/lib/api-client.ts - Typed API client with:
    • JWT token management (access token in memory, refresh via HttpOnly cookie)
    • Automatic 401 handling with token refresh retry
    • ApiError class for structured error handling
    • All API endpoint definitions (auth, invoices, contacts, dashboard, banking, etc.)
    • QueryClient with retry logic and stale time configuration
  2. src/providers/auth-provider.tsx - Authentication context:
    • useAuth hook for login/logout/refresh
    • useCurrentOrg hook for org context
    • Automatic token refresh on mount
    • Session expiry handling
  3. src/providers/index.tsx - Provider composition
  4. src/hooks/use-invoices.ts - Complete invoice API hooks:
    • useInvoices() - List with filtering/pagination
    • useInvoice() - Single invoice detail
    • useCreateInvoice() - Create mutation
    • useUpdateInvoice() - Update mutation
    • useDeleteInvoice() - Delete mutation
    • useApproveInvoice() - Approval workflow
    • useVoidInvoice() - Void mutation
    • useSendInvoice() - Send via email
    • useSendInvoiceNow() - Peppol transmission
    • useInvoiceNowStatus() - Polling status check
    • useInvoicePDF() - PDF download
  5. src/hooks/use-contacts.ts - Contact management hooks
  6. src/hooks/use-dashboard.ts - Dashboard metrics & alerts

  Updated Files:

  • src/app/layout.tsx - Added Providers wrapper
  • src/components/ui/input.tsx - Fixed React Hook conditional call
  • src/lib/gst-engine.ts - Commented unused constants

  Build Status:

  ✓ 12 static pages generated
  ✓ Zero TypeScript errors
  ✓ @tanstack/react-query installed

  Architecture Highlights:

  • State Management: Zustand (UI) + TanStack Query (server state)
  • Auth Pattern: JWT with automatic refresh, org-scoped URLs
  • Error Handling: Structured ApiError with field-level validation errors
  • Optimistic Updates: Proper cache invalidation patterns

---

  Current State (from my work):

  1. Frontend: Next.js 16.1.6 with Tailwind CSS v4, App Router
  2. Design System: "Illuminated Carbon" Neo-Brutalist Fintech aesthetic
  3. Components: Shell, Button, Input, MoneyInput, Badge, Card, Alert, Select, InvoiceLineRow, TaxBreakdownCard
  4. State Management: Zustand (UI) + TanStack Query v5 (server state)
  5. API Client: JWT auth with automatic refresh, CSRF protection
  6. Hooks: use-invoices.ts, use-contacts.ts, use-dashboard.ts, auth-provider.tsx
  7. GST Engine: Client-side calculation with Decimal.js
  8. Schema: Zod validation for invoices

---

  📝 README.md Update Summary

  Version Corrections

   Before                After
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Next.js 15            Next.js 16.1.6
   React 19              React 19.2.3
   Django Session Auth   JWT + HttpOnly Refresh Cookies

  New Sections Added

  1. Development Milestones — Documented all 4 completed milestones:
    • Milestone 1: Brutalist Foundation (design tokens, components)
    • Milestone 2: Invoice Engine (Zod schemas, GST engine)
    • Milestone 3: Data Visualization (Recharts, TanStack Table)
    • Milestone 4: API Integration (JWT client, React Query hooks)
    • Milestone 5: Polish & Testing (in progress)
  2. Enhanced Design Philosophy — Added visual language details:
    • Color palette (void, carbon, accent-primary, accent-secondary)
    • Typography stack
    • Form language (square corners, 1px borders)

  Updated Sections

  3. Technology Stack — Added:
    • TanStack Query v5
    • Zustand v5
    • Recharts v3.7
    • TanStack Table v8.21
    • JWT auth pattern
  4. File Structure — Completely rewritten to reflect actual codebase:
    • Accurate app/ router structure
    • Component organization (ui/, layout/, invoice/, dashboard/, ledger/)
    • New directories: hooks/, providers/, stores/, shared/schemas/
  5. Key Files Description — Updated to reflect actual implementations
  6. Architecture Diagram — Updated auth layer to show JWT instead of Django Session

  Authentication Flow Updated

  • Changed from Django Session cookies to JWT access tokens (15min) + HttpOnly refresh cookies (7 days)
  • Updated sequence diagram to reflect new auth flow
  • Updated security features table

  Compliance & Quality

  • Maintained all IRAS compliance mappings
  • Kept WCAG AAA accessibility documentation
  • Updated testing section (removed typecheck script reference, added build verification)

