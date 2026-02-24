import { z } from "zod";

/*
 * LEDGERSG INVOICE SCHEMA
 * IRAS 2026 Compliance Requirements:
 * - UUID required for Peppol
 * - GST precision: 4dp internal, 2dp display
 * - BCRS deposit excluded from GST base
 * - Customer UEN validation for B2B
 */

// Singapore UEN Format Validation
const uenRegex = /^[0-9]{8,9}[A-Z]$/;

// Tax Codes per IRAS
export const TAX_CODES = ["SR", "ZR", "ES", "OS", "TX", "BL", "RS"] as const;
export type TaxCode = (typeof TAX_CODES)[number];

// Tax Code Descriptions
export const TAX_CODE_DESCRIPTIONS: Record<TaxCode, string> = {
  SR: "Standard-Rated (9%)",
  ZR: "Zero-Rated (0%)",
  ES: "Exempt",
  OS: "Out-of-Scope",
  TX: "Taxable Purchase",
  BL: "Blocked Input Tax",
  RS: "Reverse Charge",
};

// Invoice Line Schema
export const invoiceLineSchema = z.object({
  id: z.string().uuid(),
  description: z.string().min(1, "Description required").max(500),
  quantity: z.string().regex(/^\d*\.?\d{0,2}$/, "Invalid quantity"),
  unit_price: z.string().regex(/^\d*\.?\d{0,4}$/, "Invalid price"),
  discount_pct: z
    .string()
    .regex(/^\d*\.?\d{0,2}$/, "Invalid discount")
    .default("0"),
  tax_code: z.enum(TAX_CODES).default("SR"),
  is_bcrs_deposit: z.boolean().default(false),
  // Computed fields (client-side preview)
  line_subtotal: z.string(),
  gst_amount: z.string(),
  line_total: z.string(),
});

// Customer Schema
export const customerSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1, "Customer name required").max(200),
  uen: z
    .string()
    .regex(uenRegex, "Invalid UEN format")
    .optional()
    .or(z.literal("")),
  gst_registration_no: z.string().optional().or(z.literal("")),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  address: z.string().max(500).optional().or(z.literal("")),
  is_peppol_enabled: z.boolean().default(false),
  peppol_id: z.string().optional().or(z.literal("")),
});

// Invoice Schema
export const invoiceSchema = z.object({
  // Identification
  id: z.string().uuid().optional(),
  invoice_number: z.string().min(1).max(50),
  uuid: z.string().uuid(), // Required for Peppol

  // Dates
  issue_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Invalid date"),
  due_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Invalid date"),
  tax_point_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Invalid date")
    .optional()
    .or(z.literal("")),

  // Customer
  customer: customerSchema,

  // Line Items
  lines: z.array(invoiceLineSchema).min(1, "At least one line item required"),

  // Financials (4dp internal precision)
  subtotal: z.string(),
  gst_rate: z.string().default("0.09"),
  gst_amount: z.string(),
  bcrs_deposit_total: z.string().default("0.00"),
  total_amount: z.string(),

  // Status
  status: z
    .enum(["DRAFT", "SENT", "PAID", "OVERDUE", "VOID"])
    .default("DRAFT"),
  peppol_status: z
    .enum(["NOT_REQUIRED", "PENDING", "SENT", "ACCEPTED", "REJECTED"])
    .default("NOT_REQUIRED"),

  // Metadata
  notes: z.string().max(1000).optional().default(""),
  reference: z.string().max(100).optional().default(""),
  terms: z.string().max(1000).optional().default(""),
});

// Output types - these represent the actual validated data
export type Invoice = z.infer<typeof invoiceSchema>;
export type InvoiceLine = z.infer<typeof invoiceLineSchema>;
export type Customer = z.infer<typeof customerSchema>;

// Input types - these represent the form input state (before defaults are applied)
export type InvoiceInput = z.input<typeof invoiceSchema>;
export type InvoiceLineInput = z.input<typeof invoiceLineSchema>;
export type CustomerInput = z.input<typeof customerSchema>;

/*
 * DEFAULT VALUES FACTORY
 */
export function createEmptyLine(): InvoiceLine {
  return {
    id: crypto.randomUUID(),
    description: "",
    quantity: "1",
    unit_price: "0.00",
    discount_pct: "0",
    tax_code: "SR",
    is_bcrs_deposit: false,
    line_subtotal: "0.0000",
    gst_amount: "0.0000",
    line_total: "0.0000",
  };
}

export function createEmptyCustomer(): Customer {
  return {
    id: crypto.randomUUID(),
    name: "",
    uen: "",
    gst_registration_no: "",
    email: "",
    address: "",
    is_peppol_enabled: false,
    peppol_id: "",
  };
}

export function getDefaultDates() {
  const today = new Date();
  const dueDate = new Date(today);
  dueDate.setDate(dueDate.getDate() + 30); // Net 30 default

  return {
    issue_date: today.toISOString().split("T")[0],
    due_date: dueDate.toISOString().split("T")[0],
  };
}

export function createEmptyInvoice(): Invoice {
  const dates = getDefaultDates();

  return {
    invoice_number: `INV-${Date.now()}`,
    uuid: crypto.randomUUID(),
    issue_date: dates.issue_date,
    due_date: dates.due_date,
    customer: createEmptyCustomer(),
    lines: [createEmptyLine()],
    subtotal: "0.0000",
    gst_rate: "0.09",
    gst_amount: "0.0000",
    bcrs_deposit_total: "0.0000",
    total_amount: "0.0000",
    status: "DRAFT",
    peppol_status: "NOT_REQUIRED",
    notes: "",
    reference: "",
    terms: "Payment due within 30 days",
  };
}
