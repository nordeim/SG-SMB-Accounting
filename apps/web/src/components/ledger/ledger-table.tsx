"use client";

import * as React from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
} from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChevronUp, ChevronDown, ChevronsUpDown, Search } from "lucide-react";
import { cn } from "@/lib/utils";

interface JournalEntry {
  id: string;
  entry_number: string;
  entry_date: string;
  account_code: string;
  account_name: string;
  description: string;
  debit: string;
  credit: string;
  reference: string;
}

// Mock data for display
const mockData: JournalEntry[] = [
  {
    id: "1",
    entry_number: "JE-2026-001",
    entry_date: "2026-01-15",
    account_code: "4100",
    account_name: "Sales Revenue",
    description: "Invoice INV-2026-001",
    debit: "0.00",
    credit: "5000.00",
    reference: "INV-001",
  },
  {
    id: "2",
    entry_number: "JE-2026-001",
    entry_date: "2026-01-15",
    account_code: "1300",
    account_name: "Accounts Receivable",
    description: "Invoice INV-2026-001",
    debit: "5450.00",
    credit: "0.00",
    reference: "INV-001",
  },
  {
    id: "3",
    entry_number: "JE-2026-001",
    entry_date: "2026-01-15",
    account_code: "2200",
    account_name: "GST Output",
    description: "Invoice INV-2026-001",
    debit: "0.00",
    credit: "450.00",
    reference: "INV-001",
  },
  {
    id: "4",
    entry_number: "JE-2026-002",
    entry_date: "2026-01-16",
    account_code: "5100",
    account_name: "Office Expenses",
    description: "Office supplies purchase",
    debit: "250.00",
    credit: "0.00",
    reference: "EXP-001",
  },
  {
    id: "5",
    entry_number: "JE-2026-002",
    entry_date: "2026-01-16",
    account_code: "1200",
    account_name: "Cash on Hand",
    description: "Office supplies purchase",
    debit: "0.00",
    credit: "272.50",
    reference: "EXP-001",
  },
  {
    id: "6",
    entry_number: "JE-2026-002",
    entry_date: "2026-01-16",
    account_code: "2100",
    account_name: "GST Input",
    description: "Office supplies purchase",
    debit: "22.50",
    credit: "0.00",
    reference: "EXP-001",
  },
];

export function LedgerTable() {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = React.useState("");

  const columns: ColumnDef<JournalEntry>[] = [
    {
      accessorKey: "entry_number",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 px-2 font-display text-xs text-text-secondary hover:text-text-primary rounded-sm"
        >
          Entry #
          {column.getIsSorted() === "asc" ? (
            <ChevronUp className="ml-1 h-3 w-3" />
          ) : column.getIsSorted() === "desc" ? (
            <ChevronDown className="ml-1 h-3 w-3" />
          ) : (
            <ChevronsUpDown className="ml-1 h-3 w-3" />
          )}
        </Button>
      ),
      cell: ({ row }) => (
        <span className="font-mono text-sm text-text-primary">
          {row.getValue("entry_number")}
        </span>
      ),
    },
    {
      accessorKey: "entry_date",
      header: "Date",
      cell: ({ row }) => (
        <span className="font-mono text-sm text-text-secondary">
          {row.getValue("entry_date")}
        </span>
      ),
    },
    {
      accessorKey: "account_code",
      header: "Account",
      cell: ({ row }) => (
        <span className="font-mono text-sm text-text-primary">
          {row.getValue("account_code")}
        </span>
      ),
    },
    {
      accessorKey: "account_name",
      header: "Name",
      cell: ({ row }) => (
        <span className="text-sm text-text-secondary">
          {row.getValue("account_name")}
        </span>
      ),
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => (
        <span className="text-sm text-text-secondary max-w-[200px] truncate block">
          {row.getValue("description")}
        </span>
      ),
    },
    {
      accessorKey: "debit",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 px-2 font-display text-xs text-text-secondary hover:text-text-primary rounded-sm"
        >
          Debit
          {column.getIsSorted() === "asc" ? (
            <ChevronUp className="ml-1 h-3 w-3" />
          ) : column.getIsSorted() === "desc" ? (
            <ChevronDown className="ml-1 h-3 w-3" />
          ) : (
            <ChevronsUpDown className="ml-1 h-3 w-3" />
          )}
        </Button>
      ),
      cell: ({ row }) => {
        const value = row.getValue("debit") as string;
        return (
          <span
            className={cn(
              "font-mono text-sm text-right tabular-nums slashed-zero block",
              value !== "0.00" ? "text-text-primary" : "text-text-muted"
            )}
          >
            {value !== "0.00" ? `S$ ${value}` : "-"}
          </span>
        );
      },
    },
    {
      accessorKey: "credit",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 px-2 font-display text-xs text-text-secondary hover:text-text-primary rounded-sm"
        >
          Credit
          {column.getIsSorted() === "asc" ? (
            <ChevronUp className="ml-1 h-3 w-3" />
          ) : column.getIsSorted() === "desc" ? (
            <ChevronDown className="ml-1 h-3 w-3" />
          ) : (
            <ChevronsUpDown className="ml-1 h-3 w-3" />
          )}
        </Button>
      ),
      cell: ({ row }) => {
        const value = row.getValue("credit") as string;
        return (
          <span
            className={cn(
              "font-mono text-sm text-right tabular-nums slashed-zero block",
              value !== "0.00" ? "text-text-primary" : "text-text-muted"
            )}
          >
            {value !== "0.00" ? `S$ ${value}` : "-"}
          </span>
        );
      },
    },
    {
      accessorKey: "reference",
      header: "Reference",
      cell: ({ row }) => (
        <span className="font-mono text-sm text-text-secondary">
          {row.getValue("reference")}
        </span>
      ),
    },
  ];

  const table = useReactTable({
    data: mockData,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            placeholder="Search entries..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="pl-9 rounded-sm border-border bg-surface"
            aria-label="Search journal entries"
          />
        </div>
      </div>

      {/* Table */}
      <div className="border border-border rounded-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-surface border-b border-border">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-border">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="hover:bg-surface/50 transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Info */}
      <div className="flex items-center justify-between text-sm text-text-secondary">
        <span>
          Showing {table.getRowModel().rows.length} of {mockData.length} entries
        </span>
      </div>
    </div>
  );
}
