import { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Plus } from "lucide-react";

export const metadata: Metadata = {
  title: "Quotes — LedgerSG",
  description: "Manage your quotes and estimates",
};

export default function QuotesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            Quotes
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Create and manage customer quotes
          </p>
        </div>
        <Button className="rounded-sm bg-accent-primary text-void hover:bg-accent-primary-dim">
          <Plus className="h-4 w-4 mr-2" />
          New Quote
        </Button>
      </div>

      <Card className="border-border bg-carbon rounded-sm">
        <CardHeader>
          <CardTitle className="font-display text-lg text-text-primary">
            Recent Quotes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-text-muted mx-auto mb-4" />
            <h3 className="text-lg font-medium text-text-primary mb-2">
              No quotes yet
            </h3>
            <p className="text-sm text-text-secondary mb-4">
              Create your first quote to get started
            </p>
            <Button
              variant="outline"
              className="rounded-sm border-border text-text-secondary"
            >
              Create Quote
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
