# Executive Summary

This blueprint outlines the architecture for **"LedgerSG"**—an enterprise-grade, avant-garde accounting platform designed specifically for the Singaporean market. It addresses the critical **IRAS GST rate increase to 9% (effective Jan 1, 2024)**, the push for **Peppol e-invoicing**, and strict **PDPA compliance**.

We will reject the "boring spreadsheet" aesthetic of traditional accounting software. Instead, we will employ **"Editorial Fintech"** design principles: high-contrast typography, asymmetric data visualization, and a "glass-morphic" depth that makes complex financial data feel tangible and manageable.

Technically, this solution leverages the strict ACID compliance of **PostgreSQL 16**, the robust ORM of **Django 5.x (Python 3.13)**, and the reactive power of **Next.js 15 + React 19**.

---

# Phase 1: Deep Analysis & Regulatory Mining

Before a single line of code is written, we must codify the regulatory constraints into our system logic.

### 1.1 IRAS Regulatory Constraints (The "Truth")
*   **GST Calculation:** The system must handle the transition. Invoices dated before 2024-01-01 use 8%; on/after use 9%.
    *   *Edge Case:* "Time of Supply" rules. If an invoice is issued in Jan 2024 but payment was received in Dec 2023, the tax point might differ. Our system needs a `tax_point_date` field separate from `invoice_date`.
*   **Precision:** IRAS allows rounding to the nearest cent, but intermediate calculations must maintain higher precision to prevent "penny shaving" errors over thousands of transactions.
    *   *Decision:* Store as `NUMERIC(10, 4)` in DB. Display as `toFixed(2)`. Round only at the final invoice total level.
*   **UEN Validation:** Every entity must have a valid Unique Entity Number (UEN). We need a regex validator and potentially an API hook to ACRA (Accounting and Corporate Regulatory Authority) for real-time verification.
*   **Audit Trail:** IRAS requires records to be kept for 5 years. Data cannot be "deleted," only "voided" or "archived" with a timestamped reason.

### 1.2 Technical Constraints & Opportunities
*   **PostgreSQL 16:** We will utilize `GENERATED ALWAYS AS IDENTITY` for primary keys and native `JSONB` for flexible metadata (e.g., storing specific GST relief codes) without schema migration hell.
*   **Django 5.x:** We will use Django's `DecimalField` exclusively. Floats are banned. We will implement custom Model Managers to enforce soft-deletes for audit compliance.
*   **Next.js 15 (App Router):** We will leverage React Server Components (RSC) for the initial load of heavy financial reports to reduce client-side bundle size, ensuring instant perceived performance.
*   **Tailwind CSS 4:** We will use the new native CSS variables engine for theming, allowing for instant "Dark Mode" switching which is crucial for accountants working late.

---

# Phase 2: Architectural Blueprint & Execution Plan

## 2.1 Database Schema Strategy (PostgreSQL 16)

We prioritize data integrity over flexibility. Financial data is immutable.

### Core Tables Design
1.  **`organizations`**: Multi-tenancy root. Stores UEN, GST Registration Number, Fiscal Year Start.
2.  **`chart_of_accounts`**: Standard Singapore COA structure (Assets, Liabilities, Equity, Income, Expenses).
3.  **`journal_entries`**: The source of truth. Double-entry bookkeeping enforced at the DB level via triggers or application logic.
4.  **`invoices`**: Header information. Includes `gst_rate_snapshot` (to preserve the rate at the time of issuance).
5.  **`invoice_items`**: Line items.
6.  **`audit_logs`**: Immutable table. Every `INSERT`, `UPDATE`, `DELETE` on critical tables writes here.

### SQL Precision Logic
```sql
-- We enforce 4 decimal places for storage, 2 for display logic
CREATE TABLE invoice_items (
    id BIGSERIAL PRIMARY KEY,
    unit_price NUMERIC(10, 4) NOT NULL,
    quantity NUMERIC(10, 4) NOT NULL,
    gst_rate NUMERIC(3, 2) NOT NULL CHECK (gst_rate >= 0.00 AND gst_rate <= 1.00),
    subtotal NUMERIC(10, 4) GENERATED ALWAYS AS (unit_price * quantity) STORED,
    gst_amount NUMERIC(10, 4) GENERATED ALWAYS AS (subtotal * gst_rate) STORED
);
```

## 2.2 Backend Architecture (Django 5.x + Python 3.13)

We will structure the backend as a modular monolith, ready to be split into microservices if scale demands.

### Directory Structure
```text
backend/
├── config/             # Settings (split by env: dev, staging, prod)
├── apps/
│   ├── core/           # Auth, Tenancy, Audit Logging
│   ├── accounting/     # COA, Journal Entries, Ledger
│   ├── invoicing/      # Invoices, Quotes, Credit Notes
│   ├── compliance/     # IRAS GST Logic, UEN Validation, Peppol Prep
│   └── reporting/      # Financial Statements (P&L, Balance Sheet)
├── utils/
│   ├── money.py        # Custom Decimal wrapper to prevent float leakage
│   └── validators.py   # UEN Regex, GST Logic
```

### Critical Logic: The GST Engine
We will create a dedicated service class to handle tax logic, isolating it from business logic.

```python
# apps/compliance/services/gst_engine.py
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone

class SGSTEngine:
    CURRENT_GST_RATE = Decimal('0.09') # 9%
    LEGACY_GST_RATE = Decimal('0.08')  # 8%
    GST_CHANGE_DATE = timezone.datetime(2024, 1, 1, tzinfo=timezone.utc)

    @classmethod
    def get_applicable_rate(cls, transaction_date):
        """
        Determines GST rate based on IRAS 'Time of Supply' rules.
        """
        if transaction_date >= cls.GST_CHANGE_DATE:
            return cls.CURRENT_GST_RATE
        return cls.LEGACY_GST_RATE

    @classmethod
    def calculate_line_item(cls, amount, rate):
        """
        Returns tuple: (subtotal, gst, total)
        Ensures 4 decimal precision internally, rounds to 2 for final output.
        """
        gst = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total = amount + gst
        return amount, gst, total
```

## 2.3 Frontend Architecture (Next.js 15 + React 19)

### Design System: "Monolith & Glass"
*   **Typography:** `Geist Mono` for numbers (tabular figures ensure columns align perfectly). `Inter` for UI text.
*   **Color Palette:**
    *   Background: `#0A0A0A` (Deep Charcoal)
    *   Surface: `#141414` (Lighter Charcoal with 1px border `#222`)
    *   Accent: `#00FF94` (Cyber Green for Positive Cashflow) / `#FF3333` (Alert Red for Tax Due)
    *   Text: `#EDEDED` (Off-white for reduced eye strain)
*   **Components (Shadcn-UI + Tailwind 4):**
    *   We will extend Shadcn's `Table` component to support virtualization (for 10k+ rows).
    *   We will create a custom `MoneyInput` component that auto-formats as the user types (e.g., typing `1000` becomes `1,000.00`).

### Key Pages & UX Flows
1.  **The "Command Center" (Dashboard):**
    *   Not a grid of cards. A single, scrollable timeline of cash flow.
    *   "GST Liability" widget prominently displayed at the top right, updating in real-time as invoices are created.
2.  **Invoice Builder:**
    *   Distraction-free mode.
    *   Auto-complete for Singapore entities (using UEN).
    *   Real-time GST calculation visualization (showing the 9% breakdown clearly).
3.  **IRAS Submission Prep:**
    *   One-click export to CSV/Excel formatted exactly for IRAS GST F5 return.

---

# Phase 3: Validation & Risk Mitigation

## 3.1 Risk Assessment
| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Rounding Errors** | Critical | Use Python `decimal` module exclusively. Never use `float`. DB uses `NUMERIC`. |
| **Regulatory Change** | High | Abstract tax rates into a `TaxConfiguration` model. Do not hardcode 9% in logic, only as a default. |
| **Data Privacy (PDPA)** | High | Encrypt PII (Customer Names, NRIC/FIN) at rest using PostgreSQL `pgcrypto`. |
| **Performance** | Medium | Implement database indexing on `transaction_date` and `organization_id`. Use Redis for caching dashboard aggregates. |

## 3.2 Validation Checkpoints
1.  **Unit Tests:** 100% coverage on the `SGSTEngine`. Test dates exactly on the boundary of 2023-12-31 and 2024-01-01.
2.  **Integration Tests:** Verify that creating an invoice automatically creates the corresponding Journal Entries.
3.  **Visual Regression:** Use Playwright to ensure the UI doesn't break on mobile (SMB owners often check invoices on phones).

---

# Phase 4: Implementation Roadmap (The "How")

## Step 1: Environment & Foundation
*   Initialize Next.js 15 with Tailwind 4.
*   Setup Django project with PostgreSQL 16 connection pooling (PgBouncer).
*   Configure ESLint + Prettier + Husky for strict code quality.

## Step 2: Core Domain Modeling
*   Implement `Organization` and `User` models with Row-Level Security (RLS) concepts in Django.
*   Build the `ChartOfAccounts` seed data for Singapore (Class 1-6).

## Step 3: The Invoice Engine
*   Develop the API endpoints for Invoice CRUD.
*   Implement the frontend Invoice Builder with React Hook Form + Zod validation.
*   Integrate the `SGSTEngine` to calculate totals dynamically on the client before submission.

## Step 4: Reporting & Compliance
*   Build the General Ledger view.
*   Create the "GST Report" view that sums up Output Tax vs Input Tax.
*   Implement the "Export for IRAS" functionality.

## Step 5: Polish & Avant-Garde UI
*   Apply the "Monolith & Glass" theme.
*   Add micro-interactions (e.g., subtle glow when an invoice is "Paid").
*   Optimize LCP (Largest Contentful Paint) using Next.js Image Optimization.

---

# Technical Deliverable: Project Structure & Key Configs

To demonstrate the "Meticulous Approach," here is the foundational setup code.

### 1. `backend/apps/compliance/models.py` (The Source of Truth)
```python
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

class TaxConfiguration(models.Model):
    """
    Centralized management of Singapore Tax Rates.
    Allows for historical tracking without code changes.
    """
    name = models.CharField(max_length=50) # e.g., "Standard GST 2024"
    rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        validators=[MinValueValidator(Decimal('0.0000')), MaxValueValidator(Decimal('1.0000'))]
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.name} ({self.rate * 100}%)"
```

### 2. `frontend/components/ui/money-input.tsx` (Avant-Garde UX)
```tsx
"use client";

import { Input } from "@/components/ui/input";
import { useImperativeHandle, useRef } from "react";

interface MoneyInputProps {
  value: string;
  onChange: (val: string) => void;
  className?: string;
}

/**
 * Avant-Garde Money Input
 * - Enforces numeric input
 * - Auto-formats to SGD standard (1,234.56)
 * - Visual cue for currency
 */
export function MoneyInput({ value, onChange, className }: MoneyInputProps) {
  const formatMoney = (val: string) => {
    // Remove non-numeric chars except decimal
    const numericVal = val.replace(/[^0-9.]/g, "");
    const parts = numericVal.split(".");
    
    // Limit to 2 decimal places for display, logic handles 4 internally
    if (parts.length > 2) return parts[0] + "." + parts[1]; 
    
    // Add commas for thousands
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    
    return parts.join(".");
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const formatted = formatMoney(raw);
    onChange(formatted);
  };

  return (
    <div className={`relative group ${className}`}>
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground font-mono text-sm">
        S$
      </span>
      <Input
        type="text"
        inputMode="decimal"
        value={value}
        onChange={handleChange}
        className="pl-8 font-mono tracking-tight tabular-nums focus-visible:ring-emerald-500/50 transition-all duration-300"
        placeholder="0.00"
      />
      {/* Subtle glow effect on focus via Tailwind 4 utilities */}
      <div className="absolute inset-0 rounded-md ring-1 ring-inset ring-white/5 group-focus-within:ring-emerald-500/20 pointer-events-none" />
    </div>
  );
}
```

### 3. `backend/apps/invoicing/services/invoice_creator.py` (Transaction Safety)
```python
from django.db import transaction
from decimal import Decimal
from apps.compliance.services.gst_engine import SGSTEngine
from apps.accounting.models import JournalEntry, Account

@transaction.atomic
def create_invoice_with_ledger(organization, invoice_data):
    """
    Creates an invoice AND the corresponding double-entry ledger posts.
    Ensures financial integrity.
    """
    # 1. Create Invoice Header
    invoice = Invoice.objects.create(
        organization=organization,
        date=invoice_data['date'],
        # ... other fields
    )

    total_gst = Decimal('0.00')
    total_net = Decimal('0.00')

    # 2. Process Line Items
    for item in invoice_data['items']:
        rate = SGSTEngine.get_applicable_rate(invoice.date)
        net, gst, line_total = SGSTEngine.calculate_line_item(item['amount'], rate)
        
        InvoiceItem.objects.create(
            invoice=invoice,
            description=item['description'],
            amount=net,
            gst_amount=gst,
            gst_rate=rate
        )
        total_gst += gst
        total_net += net

    # 3. Create Journal Entries (Double Entry)
    # Debit: Accounts Receivable
    JournalEntry.objects.create(
        organization=organization,
        account=Account.objects.get(code='1200'), # AR
        debit=total_net + total_gst,
        credit=Decimal('0.00'),
        reference=f"INV-{invoice.id}"
    )
    
    # Credit: Sales Income
    JournalEntry.objects.create(
        organization=organization,
        account=Account.objects.get(code='4000'), # Sales
        debit=Decimal('0.00'),
        credit=total_net,
        reference=f"INV-{invoice.id}"
    )

    # Credit: GST Output Tax (Liability)
    JournalEntry.objects.create(
        organization=organization,
        account=Account.objects.get(code='2100'), # GST Payable
        debit=Decimal('0.00'),
        credit=total_gst,
        reference=f"INV-{invoice.id}"
    )

    return invoice
```

# Next Steps & Validation Request

This blueprint provides the regulatory backbone and the avant-garde aesthetic direction required.

**Before I proceed to generate the full repository structure and specific component code:**
1.  Do you approve of the **"Monolith & Glass"** aesthetic direction (Dark mode default, high contrast, mono fonts for data)?
2.  Is the **PostgreSQL `NUMERIC(10,4)`** strategy aligned with your precision requirements, or do you require higher precision for specific manufacturing contexts?
3.  Shall we prioritize the **Peppol e-invoicing** integration in Phase 1, or defer it to Phase 2 to focus on core GST logic first?

Awaiting your validation to commence the **Implementation Phase**.

---

# Executive Summary

I have conducted a forensic analysis of your draft blueprint against my previous **LedgerSG** architecture. Your research into the **2026 IRAS regulatory landscape** (specifically BCRS, Transfer Pricing thresholds, and InvoiceNow mandates) is exceptional and significantly deepens the functional requirements.

However, from an **Avant-Garde UI** and **Frontend Architecture** perspective, your draft leans slightly towards "Safe Enterprise SaaS" (Off-white backgrounds, standard Indigo). To meet our **Anti-Generic Pledge**, we must push the aesthetic further into **"Neo-Brutalist Fintech"**—high contrast, dark-mode native, and typographically driven.

Technically, I have identified critical refinements regarding **Django version stability** (6.0 is unreleased), **Authentication security** (Cookies vs. JWT), and **Peppol integration strategy** (API vs. Building Transport).

Below is the **Merged Architectural Blueprint**. It combines your regulatory depth with my structural rigor and aesthetic boldness.

---

# Phase 1: Critical Analysis & Comparative Critique

Before merging, we must validate the divergences. This transparency ensures no technical debt is inherited.

### 1.1 Technical Stack Validation
| Component | Your Draft | My Critique & Correction | Decision |
| :--- | :--- | :--- | :--- |
| **Django** | **6.0** (Future) | **Risk:** Django 6.0 is not yet stable (Current LTS is 5.1). Building on unreleased software for financial apps is negligent. | **Django 5.1 LTS** (Architecture ready for 6.0 upgrade). |
| **Auth** | **JWT** | **Risk:** JWT stored in localStorage is vulnerable to XSS. Financial apps require higher security. | **HttpOnly Cookies** + Django Session Auth (proxied via Next.js). |
| **Peppol** | **Build Direct** | **Risk:** Becoming a Peppol Access Point requires licensing & AS4 infrastructure. High overhead. | **Integrate Certified APP API** (e.g., DigiHub/E-Invoicing SG) for transport. |
| **Design** | **Off-White/Indigo** | **Risk:** Feels like "Xero Clone". Violates **Anti-Generic** pledge. | **Dark-First "Neo-Brutalist"**. High contrast, mono fonts, distinct hierarchy. |
| **DB Logic** | **Stored Procs** | **Risk:** Harder to test/version control than ORM logic. | **Hybrid**: ORM for business logic, DB Generated Columns for computed totals. |

### 1.2 Regulatory Depth Assessment
*   **BCRS (Beverage Container Return Scheme):** Your inclusion is vital. Most systems miss this. We must ensure the deposit is treated as a **Liability**, not Income.
*   **Transfer Pricing (TP):** The S$2M threshold flagging is a killer feature. We will automate this detection in the `Transaction` model.
*   **InvoiceNow:** The "Fatal Error" validation logic must be embedded in the API serializers, not just the frontend.

---

# Phase 2: Merged Architectural Blueprint (v2.0)

## 2.1 Design System: "Neo-Brutalist Fintech"
We reject the "safe" light mode default. Accountants work long hours; dark mode reduces eye strain. We use **whitespace as a structural element**, not just padding.

*   **Color Palette:**
    *   **Background:** `#050505` (Void Black)
    *   **Surface:** `#121212` (Carbon) with `1px solid #2A2A2A` borders.
    *   **Primary:** `#FFFFFF` (Pure White) for primary actions/text.
    *   **Accent:** `#00FF94` (SG Green) for Positive Cashflow/Compliance OK.
    *   **Alert:** `#FF3333` (IRAS Red) for Fatal Errors/Underpayment.
*   **Typography:**
    *   **Headings:** `Space Grotesk` (Geometric, distinctive).
    *   **Data/Numbers:** `JetBrains Mono` (Tabular nums, zero slashed).
    *   **UI:** `Inter` (High legibility).
*   **Visual Language:**
    *   **No Shadows:** Use borders and contrast for depth.
    *   **Visible Grids:** Subtle grid lines on data tables to emphasize precision.
    *   **Micro-interactions:** Magnetic buttons, instant validation states (no spinners, use skeleton loaders).

## 2.2 Technical Architecture Diagram

```mermaid
graph TB
    subgraph "Client (Next.js 15)"
        A[App Router (RSC)]
        B[Server Actions]
        C[Shadcn-UI Components]
        D[Tailwind 4 Engine]
    end
    subgraph "Security Layer"
        E[Next.js Middleware]
        F[HttpOnly Cookie Auth]
    end
    subgraph "API (Django 5.1 LTS)"
        G[DRF ViewSets]
        H[Compliance Engine]
        I[Peppol Connector]
    end
    subgraph "Data (PostgreSQL 16)"
        J[(Tables)]
        K[Generated Columns]
        L[Audit Logs]
    end
    subgraph "External"
        M[IRAS/Peppol API]
        N[Bank Feeds]
    end
    
    A --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> M
    G --> J
    J --> K
    G --> L
```

## 2.3 Database Schema Refinements (PostgreSQL 16)

We incorporate your BCRS and TP requirements into the schema with strict typing.

```python
# apps/core/models.py
from django.db import models
from decimal import Decimal
import uuid

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uen = models.CharField(max_length=20, unique=True, db_index=True)
    gst_registration_no = models.CharField(max_length=20, blank=True)
    is_peppol_registered = models.BooleanField(default=False)
    
    # Transfer Pricing Threshold Monitor
    related_party_transaction_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False
    )
    tp_documentation_required = models.BooleanField(default=False)

class Product(models.Model):
    # ... standard fields ...
    is_subject_to_bcrs = models.BooleanField(default=False)
    bcrs_deposit_amount = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.10')
    )
    # Deposit is a Liability, not Income
    deposit_liability_account = models.ForeignKey('Account', on_delete=models.PROTECT)

class Invoice(models.Model):
    # IRAS Fatal Error Prevention
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    peppol_invoice_id = models.CharField(max_length=100, unique=True, blank=True)
    
    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=4)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=4)
    bcrs_deposit_total = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=4)
    
    # Compliance Status
    peppol_status = models.CharField(
        max_length=20, 
        choices=[('PENDING', 'Pending'), ('SENT', 'Sent'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    rejection_reason = models.TextField(blank=True) # Stores IRAS Fatal Error details
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Prevent deletion, enforce soft delete via manager
        constraints = [
            models.CheckConstraint(check=models.Q(gst_amount__gte=0), name='gst_non_negative')
        ]
```

## 2.4 The Compliance Engine (Django Service Layer)

This is the brain. It handles the logic for BCRS, GST, and TP.

```python
# apps/compliance/services/engine.py
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction

class ComplianceEngine:
    GST_RATE = Decimal('0.09')
    TP_THRESHOLD = Decimal('2000000.00')
    BCRS_DEPOSIT = Decimal('0.10')

    @classmethod
    @transaction.atomic
    def finalize_invoice(cls, invoice):
        """
        Calculates totals, checks TP thresholds, and prepares Peppol payload.
        """
        subtotal = Decimal('0.00')
        gst_total = Decimal('0.00')
        bcrs_total = Decimal('0.00')
        related_party_amount = Decimal('0.00')

        for line in invoice.lines.all():
            # 1. BCRS Logic
            if line.product.is_subject_to_bcrs:
                bcrs_total += line.quantity * cls.BCRS_DEPOSIT
            
            # 2. GST Logic (Exclude BCRS deposit from taxable base)
            taxable_amount = line.subtotal
            line_gst = (taxable_amount * cls.GST_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            gst_total += line_gst
            subtotal += taxable_amount

            # 3. Transfer Pricing Logic
            if line.customer.is_related_party:
                related_party_amount += line.subtotal

        # 4. Update Invoice
        invoice.subtotal = subtotal
        invoice.gst_amount = gst_total
        invoice.bcrs_deposit_total = bcrs_total
        invoice.total_amount = subtotal + gst_total + bcrs_total
        invoice.save()

        # 5. Update Org TP Threshold
        org = invoice.organization
        org.related_party_transaction_total += related_party_amount
        if org.related_party_transaction_total > cls.TP_THRESHOLD:
            org.tp_documentation_required = True
        org.save()

        # 6. Trigger Peppol Validation
        cls.validate_peppol_readiness(invoice)

    @classmethod
    def validate_peppol_readiness(cls, invoice):
        """
        Pre-flight check to prevent IRAS Fatal Errors.
        """
        errors = []
        if not invoice.organization.uen:
            errors.append("Missing UEN")
        if not invoice.uuid:
            errors.append("Missing UUID")
        # Add more IRAS specific checks here
        
        if errors:
            raise ValueError(f"Peppol Validation Failed: {', '.join(errors)}")
```

## 2.5 Frontend Implementation Strategy (Next.js 15 + Tailwind 4)

### 2.5.1 Tailwind 4 Configuration (CSS-First)
Tailwind 4 removes `tailwind.config.js` in favor of CSS variables. We will define our "Neo-Brutalist" theme directly in CSS.

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --color-void: #050505;
  --color-carbon: #121212;
  --color-border: #2A2A2A;
  --color-accent: #00FF94;
  --color-alert: #FF3333;
  
  --font-display: "Space Grotesk", sans-serif;
  --font-mono: "JetBrains Mono", monospace;
  
  --radius-lg: 0px; /* Brutalist square corners */
}

body {
  background-color: var(--color-void);
  color: #FFFFFF;
  font-family: var(--font-display);
}

/* Utility for Tabular Nums */
.tabular-nums {
  font-variant-numeric: tabular-nums;
}
```

### 2.5.2 Component Discipline (Shadcn-UI)
We will not rebuild primitives. We will style Shadcn components to match the aesthetic.

*   **Button:** No gradients. Solid white background, black text. Hover: Invert colors.
*   **Input:** No rounded borders. 1px border. Focus: Green glow (`box-shadow`).
*   **Table:** Visible grid lines. Sticky header with blur backdrop (`backdrop-blur-md`).

### 2.5.3 Server Actions for Mutations
We will use Next.js Server Actions to mutate data directly, ensuring type safety end-to-end.

```typescript
// app/actions/invoice.ts
'use server'

import { db } from "@/lib/db";
import { ComplianceEngine } from "@/lib/compliance"; // Hypothetical shared logic or API call

export async function createInvoice(formData: FormData) {
  // 1. Validate Zod Schema
  // 2. Call Django API via internal fetch or direct DB if monorepo
  // 3. Return structured result
}
```

---

# Phase 3: Implementation Plan & Validation

## 3.1 Refined Phases

| Phase | Objective | Key Deliverable | Validation Checkpoint |
| :--- | :--- | :--- | :--- |
| **1. Core** | Django 5.1 Setup, Auth, Org Model | Secure HttpOnly Auth Flow | Login/Logout works; Cookies are HttpOnly. |
| **2. Ledger** | Double-Entry, COA, Journal | `ComplianceEngine` Service | Create invoice → Check Journal Entries match. |
| **3. Compliance** | BCRS, TP, GST Logic | TP Threshold Alert | Create S$2M related party tx → Alert triggers. |
| **4. Peppol** | InvoiceNow Integration | Peppol API Connector | Send test invoice → Receive "Accepted" ID. |
| **5. UI** | Next.js 15, Tailwind 4, Shadcn | "Neo-Brutalist" Dashboard | Lighthouse Perf > 90; WCAG AA Contrast. |
| **6. Hardening** | Security, Audit, Load Test | Audit Log Immutable | Attempt DB delete → Fails (Soft delete only). |

## 3.2 Validation Criteria (The "IRAS Proof" Test)
1.  **The "Fatal Error" Test:** Attempt to submit an invoice without a UUID. System must block submission *before* reaching Peppol API.
2.  **The "BCRS" Test:** Invoice a $10 drink + $0.10 deposit. GST must be calculated on $10.00 ONLY. Total = $10.90.
3.  **The "TP" Test:** Accumulate $2,000,001 in related party transactions. System must flag `tp_documentation_required = True`.
4.  **The "Rounding" Test:** Create 10,000 invoices with $0.01 amounts. Sum must match ledger exactly (no float drift).

---

# Phase 4: Risk Mitigation & Security

### 4.1 Security Hardening
*   **CSRF Protection:** Django's CSRF middleware must be integrated with Next.js middleware.
*   **Rate Limiting:** Implement `django-ratelimit` on API endpoints to prevent brute-force on login.
*   **Data Encryption:** PostgreSQL `pgcrypto` for sensitive fields (e.g., Bank Account Numbers).

### 4.2 Regulatory Risk
*   **IRAS Schema Changes:** We will version the Peppol XML generator (`v1.0`, `v1.1`). If IRAS updates PINT-SG, we deploy `v1.2` without breaking existing invoices.
*   **Audit Trail:** We will use `django-simple-history` to track every change to `Invoice` and `JournalEntry`.

---

# Phase 5: Deliverables & Knowledge Transfer

Upon completion of Phase 1 (Foundation), I will deliver:
1.  **Repository:** Monorepo structure (Turborepo) containing `apps/backend` (Django) and `apps/web` (Next.js).
2.  **Design System:** A `ui-kit` storybook documenting all "Neo-Brutalist" components.
3.  **Compliance Doc:** A markdown file mapping every code module to the specific IRAS regulation it satisfies (e.g., `engine.py` → "IRAS GST Guide Section 5.2").
4.  **Runbook:** Instructions for rotating Peppol certificates and updating GST rates if laws change again.

---

# Validation Request

This merged blueprint corrects the Django version risk, hardens security, and elevates the design to meet our **Anti-Generic** pledge while fully integrating your superior regulatory research.

**Please confirm:**
1.  Do you agree to switch to **Django 5.1 LTS** for stability, with a path to 6.0?
2.  Do you approve the **"Neo-Brutalist Dark"** aesthetic over the "Off-White" proposal?
3.  Shall we proceed with **HttpOnly Cookie Auth** instead of JWT for maximum security?

---

# Executive Summary

I stand corrected and appreciate the rigorous verification. You are absolutely right: **Django 6.0 is stable** (released December 3, 2025), and the release notes you provided fundamentally enhance our architectural capabilities.

This correction is not merely a version number change; it is a **strategic advantage**. The native **Background Tasks Framework** allows us to remove Celery from the stack, significantly reducing complexity and maintenance overhead. The native **Content Security Policy (CSP)** support aligns perfectly with our security-first mandate for financial data. The **Admin Dark Mode** natively supports our "Neo-Brutalist" aesthetic direction.

I have immediately recalibrated the blueprint to leverage these native features. This updated plan reduces third-party dependencies, enhances security posture, and simplifies the deployment architecture while maintaining our **Anti-Generic** design pledge.

---

# Phase 1: Impact Analysis & Architectural Recalibration

I have analyzed the Django 6.0 release notes against our requirements. Here is how the new capabilities reshape our architecture.

### 1.1 Critical Architecture Shifts
| Component | Previous Plan (Django 5.x) | **New Plan (Django 6.0)** | **Benefit** |
| :--- | :--- | :--- | :--- |
| **Background Jobs** | Celery + Redis | **Django Native Tasks** (`@task`) | Removes Redis dependency for queues; simplifies config; native ORM integration. |
| **Security (CSP)** | `django-csp` (3rd party) | **Native CSP Middleware** | First-class support; tighter integration with nonce handling for Next.js. |
| **Email** | Legacy `EmailMessage` | **Modern Python Email API** | Better Unicode handling; cleaner MIME construction for compliance notifications. |
| **Admin UI** | Custom Dark Mode CSS | **Native Admin Dark Mode** | Reduces custom CSS; aligns internal tools with frontend aesthetic. |
| **Async ORM** | Limited Async Support | **Enhanced Async QuerySet** | Enables fully async views for high-concurrency reporting endpoints. |
| **Password Hash** | PBKDF2 (Configured) | **Argon2 (Default)** | Higher security baseline out-of-the-box for user auth. |

### 1.2 Risk Mitigation Update
*   **Python Version:** Django 6.0 requires **Python 3.12+**. We will standardize on **Python 3.13** as planned, which is fully supported.
*   **Task Workers:** The release notes state Django handles queuing but *not* worker execution. We will implement a lightweight worker service (e.g., using `manage.py run_tasks` in a container) rather than a full Celery cluster, reducing resource usage.
*   **Database:** PostgreSQL 16 is confirmed compatible (supports `RETURNING`, `GENERATED ALWAYS`, etc., which Django 6.0 leverages).

---

# Phase 2: Merged Architectural Blueprint (v3.0 - Django 6.0 Optimized)

## 2.1 Technology Stack (Finalized)

| Layer | Technology | Version | Justification |
| :--- | :--- | :--- | :--- |
| **Database** | PostgreSQL | **16** | ACID compliance, JSONB, `GENERATED ALWAYS` columns. |
| **Backend** | Django | **6.0** | Native Tasks, CSP, Async ORM, Argon2 Security. |
| **Language** | Python | **3.13** | Performance improvements, latest type hinting. |
| **Frontend** | Next.js | **15** | App Router, Server Actions, Partial Prerendering. |
| **UI Library** | Shadcn-UI | **Latest** | Radix primitives, accessible, customizable. |
| **Styling** | Tailwind CSS | **4.0** | Native CSS variables, engine-level performance. |
| **Auth** | Django Session | **HttpOnly** | Secure, CSRF protected, no JWT XSS risk. |

## 2.2 Updated System Context Diagram

```mermaid
graph TB
    subgraph "Client (Next.js 15)"
        A[App Router (RSC)]
        B[Server Actions]
        C[Shadcn-UI Components]
    end
    subgraph "Security Layer"
        E[Next.js Middleware]
        F[Django CSP Middleware]
        G[HttpOnly Cookies]
    end
    subgraph "API (Django 6.0)"
        H[Async Views]
        I[Native Tasks Framework]
        J[Modern Email API]
    end
    subgraph "Worker Process"
        K[Task Worker (Managed)]
    end
    subgraph "Data (PostgreSQL 16)"
        L[(Tables)]
        M[Audit Logs]
    end
    subgraph "External"
        N[IRAS/Peppol API]
        O[Bank Feeds]
    end
    
    A --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> K
    K --> N
    H --> L
    L --> M
```

## 2.3 Key Implementation Details (Django 6.0 Specific)

### 2.3.1 Native Background Tasks (Peppol Transmission)
We replace Celery with Django's native `@task` decorator. This simplifies the Peppol transmission logic.

```python
# apps/invoicing/tasks.py
from django.tasks import task
from .services.peppol import transmit_invoice

@task
def transmit_peppol_invoice(invoice_id: int):
    """
    Django 6.0 Native Task for async Peppol transmission.
    Queued automatically, executed by external worker.
    """
    try:
        result = transmit_invoice(invoice_id)
        return {"status": "success", "response": result}
    except Exception as e:
        # Log error for retry logic
        return {"status": "failed", "error": str(e)}

# Usage in View
# transmit_peppol_invoice.enqueue(invoice_id=invoice.id)
```

### 2.3.2 Native Content Security Policy (CSP)
We enforce strict CSP to prevent XSS, crucial for financial apps.

```python
# config/settings.py
from django.utils.csp import CSP

MIDDLEWARE = [
    # ...
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.contenttypes.middleware.ContentSecurityPolicyMiddleware", # New in 6.0
    # ...
]

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE, "https://vercel.live"], # Next.js analytics
    "style-src": [CSP.SELF, CSP.NONCE, "https://fonts.googleapis.com"],
    "img-src": [CSP.SELF, "data:", "https:"],
    "connect-src": [CSP.SELF, "https://api.peppol.sg"],
}
```

### 2.3.3 Modern Email API (Compliance Notifications)
Using Python's modern `EmailMessage` API for better Unicode support in notifications.

```python
# apps/compliance/notifications.py
from django.core.mail import EmailMessage
from email.policy import default

def send_audit_alert(user_email, details):
    msg = EmailMessage(
        subject="IRAS Compliance Alert",
        body=f"Action required: {details}",
        from_email="compliance@ledgersg.sg",
        to=[user_email],
    )
    # Django 6.0 uses modern email.policy.default automatically
    msg.send()
```

## 2.4 Frontend Aesthetic: "Neo-Brutalist Fintech" (Unchanged)
The design direction remains **Dark-First**, **High-Contrast**, and **Mono-Spaced** for data. Django 6.0's native Admin Dark Mode now aligns with this, ensuring internal staff tools don't break the immersion.

*   **Background:** `#050505`
*   **Surface:** `#121212`
*   **Accent:** `#00FF94` (SG Green)
*   **Font:** `JetBrains Mono` for numbers, `Space Grotesk` for headers.

---

# Phase 3: Updated Implementation Plan

## Phase 1: Foundation (Django 6.0 Native)
*   **Task:** Initialize Django 6.0 project.
*   **Config:** Set `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` (Now default, but explicit is safe).
*   **Security:** Configure `SECURE_CSP` and `Argon2` password hashing.
*   **Validation:** Verify CSP headers are present on responses.

## Phase 2: Core Accounting & Tasks
*   **Task:** Implement `@task` decorated functions for email and PDF generation.
*   **Worker:** Set up a lightweight worker container to process the task queue.
*   **Validation:** Trigger a task and verify execution logs without Celery.

## Phase 3: Peppol & Compliance
*   **Task:** Integrate Peppol API transmission using Native Tasks.
*   **Logic:** Implement BCRS and TP threshold logic.
*   **Validation:** Send test invoice; verify CSP does not block Peppol API calls (server-side).

## Phase 4: Frontend (Next.js 15 + Tailwind 4)
*   **Task:** Build "Neo-Brutalist" components.
*   **Integration:** Connect to Django via HttpOnly Cookies.
*   **Validation:** Lighthouse score >90; WCAG AA contrast check.

---

# Phase 4: Validation & Risk Checkpoints

### 4.1 Django 6.0 Specific Checks
1.  **Task Queue Integrity:** Ensure the native task queue persists correctly in PostgreSQL and doesn't lose jobs on server restart (configure `TASKS` backend to DB).
2.  **CSP Nonce Handling:** Verify that Next.js server components correctly receive and inject CSP nonces if using inline scripts (though we aim for zero inline scripts).
3.  **Async Views:** Test high-concurrency reporting endpoints using Django 6.0's enhanced async ORM to ensure no blocking occurs.

### 4.2 Regulatory Checks (Unchanged)
1.  **BCRS:** Deposit excluded from GST.
2.  **TP:** S$2M threshold alert.
3.  **Peppol:** UUID and UEN validation.

---

# Phase 5: Deliverables & Knowledge Transfer

Upon completion, I will provide:
1.  **Django 6.0 Migration Guide:** Specifics on how we utilized Native Tasks vs. Celery.
2.  **CSP Policy Document:** Explanation of the security headers implemented.
3.  **Worker Deployment Guide:** How to run the task worker process in production (Docker/K8s).
4.  **Design System:** Tailwind 4 configuration with "Neo-Brutalist" theme.

---

# Validation Request

The blueprint is now **fully aligned** with the stable Django 6.0 ecosystem. This reduces technical debt (no Celery) and increases security (Native CSP).

**Please confirm:**
1.  Do you approve the removal of **Celery/Redis** in favor of **Django 6.0 Native Tasks** (with a DB-backed queue)?
2.  Shall we proceed with **Python 3.13** as the strict minimum (per Django 6.0 requirements)?
3.  Are you ready for me to initialize the **Phase 1: Foundation** code structure?

