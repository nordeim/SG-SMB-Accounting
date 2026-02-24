import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import type { InvoiceLine, TaxCode } from "@/shared/schemas/invoice";
import type { InvoiceTotals } from "@/lib/gst-engine";

/*
 * LEDGERSG INVOICE STORE
 *
 * Purpose: Manage UI state ONLY (not form data)
 * Form data is managed by React Hook Form (single source of truth)
 *
 * This store handles:
 * - Sidebar collapse state
 * - Compact mode toggle
 * - BCRS toggle global state
 * - Unsaved changes warning
 * - Current calculation totals (for display components)
 */

interface InvoiceUIState {
  // UI State
  sidebarCollapsed: boolean;
  compactMode: boolean;
  bcrsEnabled: boolean;
  hasUnsavedChanges: boolean;

  // Calculation State (read-only, updated by form)
  currentTotals: InvoiceTotals | null;

  // Actions
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleCompactMode: () => void;
  toggleBCRS: () => void;
  setHasUnsavedChanges: (hasChanges: boolean) => void;
  updateTotals: (totals: InvoiceTotals) => void;
  resetStore: () => void;
}

const initialState = {
  sidebarCollapsed: false,
  compactMode: false,
  bcrsEnabled: false,
  hasUnsavedChanges: false,
  currentTotals: null,
};

export const useInvoiceStore = create<InvoiceUIState>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

    toggleCompactMode: () =>
      set((state) => ({ compactMode: !state.compactMode })),

    toggleBCRS: () => {
      const bcrsEnabled = !get().bcrsEnabled;
      set({ bcrsEnabled, hasUnsavedChanges: true });
    },

    setHasUnsavedChanges: (hasChanges) => set({ hasUnsavedChanges: hasChanges }),

    updateTotals: (totals) => set({ currentTotals: totals }),

    resetStore: () => set(initialState),
  }))
);

/*
 * HELPER: Create new invoice line template
 */
export function createInvoiceLine(): InvoiceLine {
  return {
    id: crypto.randomUUID(),
    description: "",
    quantity: "1",
    unit_price: "0.00",
    discount_pct: "0",
    tax_code: "SR" as TaxCode,
    is_bcrs_deposit: false,
    line_subtotal: "0.0000",
    gst_amount: "0.0000",
    line_total: "0.0000",
  };
}
