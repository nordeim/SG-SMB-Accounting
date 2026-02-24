import { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { LedgerTable } from "@/components/ledger/ledger-table";

export const metadata: Metadata = {
  title: "General Ledger — LedgerSG",
  description: "View your general ledger and journal entries",
};

export default function LedgerPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            General Ledger
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            View and manage journal entries
          </p>
        </div>
        <Button className="rounded-sm bg-accent-primary text-void hover:bg-accent-primary-dim">
          <Plus className="h-4 w-4 mr-2" />
          New Entry
        </Button>
      </div>

      <Card className="border-border bg-carbon rounded-sm">
        <CardHeader>
          <CardTitle className="font-display text-lg text-text-primary">
            Journal Entries
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LedgerTable />
        </CardContent>
      </Card>
    </div>
  );
}
