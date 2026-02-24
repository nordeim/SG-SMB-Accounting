import { Decimal } from "decimal.js";
import type { InvoiceLine, TaxCode } from "@/shared/schemas/invoice";

/*
 * LEDGERSG GST CALCULATION ENGINE
 *
 * CRITICAL: This is CLIENT-SIDE PREVIEW ONLY.
 * Authoritative calculation happens server-side in Django ComplianceEngine.
 *
 * Precision Rules (IRAS Compliant):
 * - Internal: 4 decimal places (NUMERIC(10,4))
 * - Display: 2 decimal places (ROUND_HALF_UP)
 * - GST Fraction for inclusive: 9/109 for 9% rate
 */

// Decimal.js configuration
Decimal.set({
  precision: 20,
  rounding: Decimal.ROUND_HALF_UP,
  toExpNeg: -7,
  toExpPos: 21,
});

// Precision constants (for future use in rounding operations)
// const FOUR_DP = new Decimal("0.0001");
// const TWO_DP = new Decimal("0.01");

// Singapore GST Rates
const GST_RATES: Record<TaxCode, Decimal> = {
  SR: new Decimal("0.09"), // Standard-rated 9%
  ZR: new Decimal("0"), // Zero-rated
  ES: new Decimal("0"), // Exempt
  OS: new Decimal("0"), // Out-of-scope
  TX: new Decimal("0.09"), // Taxable purchase
  BL: new Decimal("0.09"), // Blocked input tax
  RS: new Decimal("0.09"), // Reverse charge
};

// Tax fraction for GST-inclusive extraction (9/109 for 9% rate)
export const GST_FRACTION = new Decimal("9").div(new Decimal("109"));

export interface LineGSTResult {
  line_subtotal: string; // Net before GST (4dp internal)
  gst_amount: string; // GST component (4dp internal)
  line_total: string; // Gross including GST (4dp internal)
  display_subtotal: string; // 2dp for display
  display_gst: string; // 2dp for display
  display_total: string; // 2dp for display
  is_bcrs_exempt: boolean; // BCRS deposit not subject to GST
}

export interface InvoiceTotals {
  subtotal: string;
  gst_amount: string;
  bcrs_deposit_total: string;
  total_amount: string;
  display_subtotal: string;
  display_gst: string;
  display_bcrs: string;
  display_total: string;
}

/**
 * Calculate GST for a single invoice line
 *
 * BCRS deposits are NOT subject to GST (IRAS regulation)
 */
export function calculateLineGST(
  quantity: string,
  unit_price: string,
  discount_pct: string,
  tax_code: TaxCode,
  is_bcrs_deposit: boolean = false
): LineGSTResult {
  const qty = new Decimal(quantity || "0");
  const price = new Decimal(unit_price || "0");
  const discount = new Decimal(discount_pct || "0");
  const rate = GST_RATES[tax_code] || new Decimal("0");

  // Line amount = qty × price × (1 - discount/100)
  const line_subtotal = qty
    .mul(price)
    .mul(new Decimal("1").minus(discount.div("100")))
    .toDecimalPlaces(4, Decimal.ROUND_HALF_UP);

  let gst_amount: Decimal;
  let line_total: Decimal;

  // BCRS deposits are NOT subject to GST
  if (is_bcrs_deposit) {
    gst_amount = new Decimal("0");
    line_total = line_subtotal;
  } else if (rate.isZero()) {
    // Zero-rated, exempt, or out-of-scope
    gst_amount = new Decimal("0");
    line_total = line_subtotal;
  } else {
    // Standard GST calculation
    gst_amount = line_subtotal
      .mul(rate)
      .toDecimalPlaces(4, Decimal.ROUND_HALF_UP);
    line_total = line_subtotal.add(gst_amount);
  }

  return {
    line_subtotal: line_subtotal.toFixed(4),
    gst_amount: gst_amount.toFixed(4),
    line_total: line_total.toFixed(4),
    display_subtotal: line_subtotal.toDecimalPlaces(2).toFixed(2),
    display_gst: gst_amount.toDecimalPlaces(2).toFixed(2),
    display_total: line_total.toDecimalPlaces(2).toFixed(2),
    is_bcrs_exempt: is_bcrs_deposit,
  };
}

/**
 * Calculate invoice totals from all lines
 *
 * Per IRAS: Sum line-level GST, don't calculate on totals
 */
export function calculateInvoiceTotals(lines: LineGSTResult[]): InvoiceTotals {
  let subtotal = new Decimal("0");
  let gst_amount = new Decimal("0");
  let bcrs_deposit_total = new Decimal("0");

  for (const line of lines) {
    const lineSubtotal = new Decimal(line.line_subtotal);
    const lineGst = new Decimal(line.gst_amount);

    if (line.is_bcrs_exempt) {
      bcrs_deposit_total = bcrs_deposit_total.add(lineSubtotal);
    } else {
      subtotal = subtotal.add(lineSubtotal);
      gst_amount = gst_amount.add(lineGst);
    }
  }

  const total_amount = subtotal.add(gst_amount).add(bcrs_deposit_total);

  return {
    subtotal: subtotal.toFixed(4),
    gst_amount: gst_amount.toFixed(4),
    bcrs_deposit_total: bcrs_deposit_total.toFixed(4),
    total_amount: total_amount.toFixed(4),
    display_subtotal: subtotal.toDecimalPlaces(2).toFixed(2),
    display_gst: gst_amount.toDecimalPlaces(2).toFixed(2),
    display_bcrs: bcrs_deposit_total.toDecimalPlaces(2).toFixed(2),
    display_total: total_amount.toDecimalPlaces(2).toFixed(2),
  };
}

/**
 * Calculate from InvoiceLine objects directly
 */
export function calculateFromLines(lines: InvoiceLine[]): {
  lineResults: LineGSTResult[];
  totals: InvoiceTotals;
} {
  const lineResults = lines.map((line) =>
    calculateLineGST(
      line.quantity,
      line.unit_price,
      line.discount_pct,
      line.tax_code,
      line.is_bcrs_deposit
    )
  );

  const totals = calculateInvoiceTotals(lineResults);

  return { lineResults, totals };
}

/**
 * Validate GST calculation matches server response
 * Used for reconciliation after form submission
 */
export function validateGSTCalculation(
  clientTotals: InvoiceTotals,
  serverTotals: { subtotal: string; gst_amount: string; total_amount: string }
): { valid: boolean; discrepancies: string[] } {
  const discrepancies: string[] = [];
  const tolerance = new Decimal("0.01"); // 1 cent tolerance for rounding

  if (
    new Decimal(clientTotals.subtotal)
      .minus(serverTotals.subtotal)
      .abs()
      .greaterThan(tolerance)
  ) {
    discrepancies.push(
      `Subtotal mismatch: client=${clientTotals.display_subtotal}, server=${serverTotals.subtotal}`
    );
  }

  if (
    new Decimal(clientTotals.gst_amount)
      .minus(serverTotals.gst_amount)
      .abs()
      .greaterThan(tolerance)
  ) {
    discrepancies.push(
      `GST mismatch: client=${clientTotals.display_gst}, server=${serverTotals.gst_amount}`
    );
  }

  if (
    new Decimal(clientTotals.total_amount)
      .minus(serverTotals.total_amount)
      .abs()
      .greaterThan(tolerance)
  ) {
    discrepancies.push(
      `Total mismatch: client=${clientTotals.display_total}, server=${serverTotals.total_amount}`
    );
  }

  return {
    valid: discrepancies.length === 0,
    discrepancies,
  };
}

/**
 * Format currency for display
 */
export function formatCurrency(amount: string | number | Decimal): string {
  const value = amount instanceof Decimal ? amount : new Decimal(amount || 0);
  return `S$ ${value.toDecimalPlaces(2).toFixed(2)}`;
}

/**
 * Get GST rate percentage for display
 */
export function getGSTRatePercentage(taxCode: TaxCode): string {
  const rate = GST_RATES[taxCode];
  return `${rate.mul(100).toFixed(0)}%`;
}
