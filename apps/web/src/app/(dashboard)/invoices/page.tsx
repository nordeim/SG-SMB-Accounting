import { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Plus, Search } from "lucide-react";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Invoices — LedgerSG",
  description: "Manage your invoices and quotes",
};

// Mock data for display
const mockInvoices = [
  {
    id: "inv-1",
    number: "INV-2026-001",
    customer: "ABC Pte Ltd",
    date: "2026-01-15",
    dueDate: "2026-02-14",
    amount: "5,400.00",
    status: "SENT",
  },
  {
    id: "inv-2",
    number: "INV-2026-002",
    customer: "XYZ Corporation",
    date: "2026-01-20",
    dueDate: "2026-02-19",
    amount: "12,300.00",
    status: "PAID",
  },
  {
    id: "inv-3",
    number: "INV-2026-003",
    customer: "Singapore Tech Solutions",
    date: "2026-01-22",
    dueDate: "2026-02-21",
    amount: "8,750.00",
    status: "DRAFT",
  },
];

function getStatusBadgeClass(status: string) {
  switch (status) {
    case "PAID":
      return "bg-accent-primary text-void";
    case "SENT":
      return "bg-accent-secondary text-void";
    case "DRAFT":
      return "bg-surface text-text-secondary border border-border";
    case "OVERDUE":
      return "bg-alert text-white";
    default:
      return "bg-surface text-text-secondary";
  }
}

export default function InvoicesPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            Invoices
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage your sales invoices and track payments
          </p>
        </div>
        <Link href="/invoices/new">
          <Button className="rounded-sm bg-accent-primary text-void hover:bg-accent-primary-dim">
            <Plus className="h-4 w-4 mr-2" />
            New Invoice
          </Button>
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search invoices..."
            className="w-full pl-9 pr-4 py-2 rounded-sm border border-border bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/50"
          />
        </div>
        <Button
          variant="outline"
          className="rounded-sm border-border text-text-secondary"
        >
          Filter
        </Button>
      </div>

      {/* Invoices Table */}
      <Card className="border-border bg-carbon rounded-sm">
        <CardHeader>
          <CardTitle className="font-display text-lg text-text-primary">
            Recent Invoices
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-3 text-xs font-medium text-text-secondary uppercase">
                    Invoice
                  </th>
                  <th className="pb-3 text-xs font-medium text-text-secondary uppercase">
                    Customer
                  </th>
                  <th className="pb-3 text-xs font-medium text-text-secondary uppercase">
                    Date
                  </th>
                  <th className="pb-3 text-xs font-medium text-text-secondary uppercase">
                    Due Date
                  </th>
                  <th className="pb-3 text-xs font-medium text-text-secondary uppercase text-right">
                    Amount
                  </th>
                  <th className="pb-3 text-xs font-medium text-text-secondary uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {mockInvoices.map((invoice) => (
                  <tr
                    key={invoice.id}
                    className="hover:bg-surface/50 transition-colors"
                  >
                    <td className="py-4">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-text-muted" />
                        <span className="font-mono text-sm text-text-primary">
                          {invoice.number}
                        </span>
                      </div>
                    </td>
                    <td className="py-4">
                      <span className="text-sm text-text-secondary">
                        {invoice.customer}
                      </span>
                    </td>
                    <td className="py-4">
                      <span className="text-sm font-mono text-text-secondary">
                        {invoice.date}
                      </span>
                    </td>
                    <td className="py-4">
                      <span className="text-sm font-mono text-text-secondary">
                        {invoice.dueDate}
                      </span>
                    </td>
                    <td className="py-4 text-right">
                      <span className="text-sm font-mono font-medium text-text-primary tabular-nums">
                        S$ {invoice.amount}
                      </span>
                    </td>
                    <td className="py-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium ${getStatusBadgeClass(
                          invoice.status
                        )}`}
                      >
                        {invoice.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
