import { z } from "zod";

/*
 * LEDGERSG DASHBOARD SCHEMA
 *
 * Purpose: Type-safe dashboard metrics with IRAS compliance context
 */

// GST Threshold Status
export const GST_THRESHOLD_STATUS = ["SAFE", "WARNING", "CRITICAL", "EXCEEDED"] as const;
export type GSTThresholdStatus = (typeof GST_THRESHOLD_STATUS)[number];

// Compliance Alert Severity
export const ALERT_SEVERITY = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;
export type AlertSeverity = (typeof ALERT_SEVERITY)[number];

// Compliance Alert Schema
export const complianceAlertSchema = z.object({
  id: z.string().uuid(),
  severity: z.enum(ALERT_SEVERITY),
  title: z.string(),
  message: z.string(),
  action_required: z.string(),
  deadline: z.string().optional(), // ISO date
  dismissed: z.boolean().default(false),
});

// GST Period Schema
export const gstPeriodSchema = z.object({
  start_date: z.string(),
  end_date: z.string(),
  filing_due_date: z.string(),
  days_remaining: z.number(),
});

// Dashboard Metrics Schema
export const dashboardMetricsSchema = z.object({
  // Financial Metrics
  gst_payable: z.string(), // 4dp internal
  gst_payable_display: z.string(), // 2dp display
  outstanding_receivables: z.string(),
  outstanding_payables: z.string(),
  revenue_mtd: z.string(),
  revenue_ytd: z.string(),
  cash_on_hand: z.string(),

  // GST Threshold Monitoring (IRAS Compliance)
  gst_threshold_status: z.enum(GST_THRESHOLD_STATUS),
  gst_threshold_utilization: z.number(), // 0-100 percentage
  gst_threshold_amount: z.string(), // Current rolling 12-month taxable turnover
  gst_threshold_limit: z.string(), // S$1,000,000

  // Compliance Alerts
  compliance_alerts: z.array(complianceAlertSchema),

  // Invoice Statistics
  invoices_pending: z.number(),
  invoices_overdue: z.number(),
  invoices_peppol_pending: z.number(),

  // Period Info
  current_gst_period: gstPeriodSchema,

  // Last Updated
  last_updated: z.string(), // ISO timestamp
});

export type DashboardMetrics = z.infer<typeof dashboardMetricsSchema>;
export type ComplianceAlert = z.infer<typeof complianceAlertSchema>;
export type GSTPeriod = z.infer<typeof gstPeriodSchema>;

/*
 * MOCK DATA FACTORY
 */
export function createMockDashboardMetrics(): DashboardMetrics {
  return {
    gst_payable: "12450.0000",
    gst_payable_display: "12,450.00",
    outstanding_receivables: "45,230.50",
    outstanding_payables: "23,100.00",
    revenue_mtd: "125,000.00",
    revenue_ytd: "1,450,000.00",
    cash_on_hand: "89,450.25",
    gst_threshold_status: "WARNING",
    gst_threshold_utilization: 78,
    gst_threshold_amount: "780,000.00",
    gst_threshold_limit: "1,000,000.00",
    compliance_alerts: [
      {
        id: "alert-1",
        severity: "HIGH",
        title: "GST F5 Filing Due Soon",
        message: "Your GST F5 return is due in 7 days",
        action_required: "File GST F5 return",
        deadline: "2026-01-31",
        dismissed: false,
      },
      {
        id: "alert-2",
        severity: "MEDIUM",
        title: "3 Invoices Overdue",
        message: "You have 3 invoices that are past their due date",
        action_required: "Follow up on overdue invoices",
        dismissed: false,
      },
    ],
    invoices_pending: 12,
    invoices_overdue: 3,
    invoices_peppol_pending: 2,
    current_gst_period: {
      start_date: "2026-01-01",
      end_date: "2026-03-31",
      filing_due_date: "2026-04-30",
      days_remaining: 65,
    },
    last_updated: new Date().toISOString(),
  };
}
