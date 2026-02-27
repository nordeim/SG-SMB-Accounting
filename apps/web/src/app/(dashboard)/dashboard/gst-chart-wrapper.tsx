"use client";

import { useState, useEffect } from "react";
import { GSTF5Chart } from "@/components/dashboard/gst-f5-chart";

interface GSTChartWrapperProps {
  gstPayable: string;
}

export function GSTChartWrapper({ gstPayable }: GSTChartWrapperProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="h-[200px] bg-surface/50 rounded-sm flex items-center justify-center">
        <span className="text-text-muted text-sm">Loading chart...</span>
      </div>
    );
  }

  return <GSTF5Chart gstPayable={gstPayable} />;
}
