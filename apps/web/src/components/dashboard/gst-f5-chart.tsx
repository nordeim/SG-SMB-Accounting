"use client";

import * as React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// Brutalist color palette for charts
const CHART_COLORS = {
  primary: "#00E585",
  secondary: "#D4A373",
  alert: "#FF3333",
  warning: "#FFB347",
  muted: "#666666",
};

// GST F5 Box data structure
interface F5BoxData {
  box: string;
  label: string;
  value: number;
  color: string;
}

interface GSTF5ChartProps {
  gstPayable: string;
  outputTax?: string;
  inputTax?: string;
}

export function GSTF5Chart({
  gstPayable,
  outputTax = "15000.00",
  inputTax = "2550.00",
}: GSTF5ChartProps) {
  const [showTable, setShowTable] = React.useState(false);

  const chartData: F5BoxData[] = [
    { box: "Box 1", label: "Standard-Rated", value: 150000, color: CHART_COLORS.primary },
    { box: "Box 2", label: "Zero-Rated", value: 25000, color: CHART_COLORS.secondary },
    { box: "Box 6", label: "Output Tax", value: parseFloat(outputTax), color: CHART_COLORS.primary },
    { box: "Box 7", label: "Input Tax", value: parseFloat(inputTax), color: CHART_COLORS.secondary },
    { box: "Box 8", label: "Net GST", value: parseFloat(gstPayable.replace(/,/g, "")), color: CHART_COLORS.alert },
  ];

  // Custom tooltip for brutalist aesthetic
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: F5BoxData }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Card className="border-border bg-carbon p-3 rounded-sm shadow-none border">
          <p className="font-mono text-xs text-text-secondary">{data.label}</p>
          <p className="font-mono text-lg text-accent-primary">
            S$ {data.value.toLocaleString()}
          </p>
        </Card>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Chart Toggle for Accessibility */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowTable(!showTable)}
          className="text-xs text-text-secondary hover:text-accent-primary underline"
          aria-label={showTable ? "Show chart view" : "Show data table view"}
        >
          {showTable ? "Show Chart" : "Show Data Table"}
        </button>
      </div>

      {showTable ? (
        /* Accessible Data Table Alternative */
        <div
          role="table"
          aria-label="GST F5 Return Breakdown"
          className="border border-border rounded-sm"
        >
          <div role="rowheader" className="grid grid-cols-3 border-b border-border bg-surface text-xs font-medium text-text-secondary">
            <div role="columnheader" className="p-2 border-r border-border">Box</div>
            <div role="columnheader" className="p-2 border-r border-border">Description</div>
            <div role="columnheader" className="p-2 text-right">Amount</div>
          </div>
          {chartData.map((row) => (
            <div
              key={row.box}
              role="row"
              className="grid grid-cols-3 border-b border-border last:border-0 text-sm"
            >
              <div role="cell" className="p-2 border-r border-border font-mono text-text-primary">
                {row.box}
              </div>
              <div role="cell" className="p-2 border-r border-border text-text-secondary">
                {row.label}
              </div>
              <div
                role="cell"
                className={cn(
                  "p-2 text-right font-mono",
                  row.box === "Box 8" ? "text-alert font-bold" : "text-text-primary"
                )}
              >
                S$ {row.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Visual Chart */
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <XAxis
                dataKey="box"
                tick={{
                  fill: "#A0A0A0",
                  fontSize: 10,
                  fontFamily: "JetBrains Mono",
                }}
                axisLine={{ stroke: "#2A2A2A" }}
                tickLine={{ stroke: "#2A2A2A" }}
              />
              <YAxis
                tick={{
                  fill: "#A0A0A0",
                  fontSize: 10,
                  fontFamily: "JetBrains Mono",
                }}
                axisLine={{ stroke: "#2A2A2A" }}
                tickLine={{ stroke: "#2A2A2A" }}
                tickFormatter={(value: number) =>
                  value >= 1000 ? `S$${(value / 1000).toFixed(0)}k` : `S$${value}`
                }
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" radius={[0, 0, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Screen Reader Summary */}
      <div className="sr-only" aria-live="polite">
        GST F5 Breakdown: Box 1 Standard-Rated Supplies S${" "}
        {chartData[0].value.toLocaleString()}, Box 2 Zero-Rated Supplies S${" "}
        {chartData[1].value.toLocaleString()}, Box 6 Output Tax S${" "}
        {chartData[2].value.toLocaleString()}, Box 7 Input Tax S${" "}
        {chartData[3].value.toLocaleString()}, Box 8 Net GST Payable S${" "}
        {gstPayable}
      </div>
    </div>
  );
}
