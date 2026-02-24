import { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PieChart, Download } from "lucide-react";

export const metadata: Metadata = {
  title: "Reports — LedgerSG",
  description: "Generate financial reports and statements",
};

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            Reports
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Generate and export financial reports
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[
          {
            title: "Profit & Loss",
            description: "Income statement for a specific period",
          },
          {
            title: "Balance Sheet",
            description: "Assets, liabilities, and equity",
          },
          {
            title: "GST F5 Return",
            description: "IRAS GST return form",
          },
          {
            title: "Trial Balance",
            description: "Summary of all ledger accounts",
          },
          {
            title: "General Ledger",
            description: "Detailed transaction history",
          },
          {
            title: "Aged Receivables",
            description: "Outstanding customer invoices",
          },
        ].map((report) => (
          <Card
            key={report.title}
            className="border-border bg-carbon rounded-sm hover:border-accent-primary/50 transition-colors"
          >
            <CardHeader>
              <div className="flex items-center gap-2">
                <PieChart className="h-5 w-5 text-accent-primary" />
                <CardTitle className="font-display text-base text-text-primary">
                  {report.title}
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-secondary mb-4">
                {report.description}
              </p>
              <Button
                variant="outline"
                size="sm"
                className="rounded-sm border-border text-text-secondary w-full"
              >
                <Download className="h-4 w-4 mr-2" />
                Generate
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
