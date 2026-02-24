import { useQuery } from "@tanstack/react-query";
import { api, endpoints } from "@/lib/api-client";
import type { DashboardMetrics } from "@/shared/schemas/dashboard";

// Dashboard metrics
export function useDashboardMetrics(orgId: string) {
  return useQuery({
    queryKey: [orgId, "dashboard", "metrics"],
    queryFn: async () => {
      const response = await api.get<DashboardMetrics>(
        endpoints.dashboard(orgId).metrics
      );
      return response;
    },
    enabled: !!orgId,
    // Refresh every 5 minutes
    refetchInterval: 5 * 60 * 1000,
    // Stale after 1 minute
    staleTime: 60 * 1000,
  });
}

// Compliance alerts
export function useComplianceAlerts(orgId: string) {
  return useQuery({
    queryKey: [orgId, "dashboard", "alerts"],
    queryFn: async () => {
      const response = await api.get<{
        results: Array<{
          id: string;
          severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
          title: string;
          message: string;
          action_required: string;
          deadline?: string;
          dismissed: boolean;
        }>;
      }>(endpoints.dashboard(orgId).alerts);
      return response.results;
    },
    enabled: !!orgId,
    refetchInterval: 60 * 1000, // Refresh every minute
  });
}

// GST F5 Return computation
export function useGSTF5Compute(orgId: string, periodId?: string) {
  return useQuery({
    queryKey: [orgId, "gst", "f5-compute", periodId],
    queryFn: async () => {
      const url = periodId
        ? `/api/v1/${orgId}/gst/f5-compute/?period_id=${periodId}`
        : `/api/v1/${orgId}/gst/f5-compute/`;
      const response = await api.get<{
        box1: string; // Standard-rated supplies
        box2: string; // Zero-rated supplies
        box3: string; // Exempt supplies
        box4: string; // Total supplies
        box5: string; // Total purchases
        box6: string; // Output tax
        box7: string; // Input tax
        box8: string; // Net GST
        box9: string; // Total input tax
        box10: string; // Total output tax
        box11: string; // Total input tax claimed
        box12: string; // Total output tax due
        box13: string; // Total GST payable
        box14: string; // Total GST refundable
        box15: string; // Total GST due
      }>(url);
      return response;
    },
    enabled: !!orgId,
  });
}

// Recent activity / audit log
export function useRecentActivity(orgId: string, limit: number = 10) {
  return useQuery({
    queryKey: [orgId, "dashboard", "activity", limit],
    queryFn: async () => {
      const response = await api.get<{
        results: Array<{
          id: string;
          action: string;
          entity_type: string;
          entity_id: string;
          description: string;
          created_at: string;
          user: {
            id: string;
            full_name: string;
          };
        }>;
      }>(`/api/v1/${orgId}/audit-log/?limit=${limit}`);
      return response.results;
    },
    enabled: !!orgId,
  });
}
