import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, endpoints } from "@/lib/api-client";
import { toast } from "@/hooks/use-toast";
import type { Invoice, InvoiceInput } from "@/shared/schemas/invoice";

// List invoices with optional filters
export function useInvoices(
  orgId: string,
  filters?: {
    status?: string;
    document_type?: string;
    search?: string;
    date_from?: string;
    date_to?: string;
  }
) {
  const queryString = filters
    ? "?" + new URLSearchParams(Object.entries(filters).filter(([, v]) => v)).toString()
    : "";

  return useQuery({
    queryKey: [orgId, "invoices", filters],
    queryFn: async () => {
      const response = await api.get<{
        results: Invoice[];
        count: number;
        next?: string;
        previous?: string;
      }>(endpoints.invoices(orgId).list + queryString);
      return response;
    },
    enabled: !!orgId,
  });
}

// Get single invoice detail
export function useInvoice(orgId: string, invoiceId: string) {
  return useQuery({
    queryKey: [orgId, "invoices", invoiceId],
    queryFn: async () => {
      const response = await api.get<Invoice>(
        endpoints.invoices(orgId).detail(invoiceId)
      );
      return response;
    },
    enabled: !!orgId && !!invoiceId,
  });
}

// Create invoice
export function useCreateInvoice(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: InvoiceInput) => {
      const response = await api.post<Invoice>(
        endpoints.invoices(orgId).list,
        data
      );
      return response;
    },
    onSuccess: () => {
      toast({
        title: "Invoice created",
        description: "Your invoice has been created successfully.",
        variant: "success",
      });
      // Invalidate invoices list
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices"] });
      // Invalidate dashboard metrics
      queryClient.invalidateQueries({ queryKey: [orgId, "dashboard"] });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to create invoice",
        description: error.message || "An error occurred while creating the invoice.",
        variant: "error",
      });
    },
  });
}

// Update invoice (only for DRAFT status)
export function useUpdateInvoice(orgId: string, invoiceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<InvoiceInput>) => {
      const response = await api.patch<Invoice>(
        endpoints.invoices(orgId).detail(invoiceId),
        data
      );
      return response;
    },
    onSuccess: () => {
      toast({
        title: "Invoice updated",
        description: "Your invoice has been updated successfully.",
        variant: "success",
      });
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices", invoiceId] });
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices"] });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to update invoice",
        description: error.message || "An error occurred while updating the invoice.",
        variant: "error",
      });
    },
  });
}

// Approve invoice (DRAFT -> APPROVED)
export function useApproveInvoice(orgId: string, invoiceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post<Invoice>(
        endpoints.invoices(orgId).approve(invoiceId),
        {}
      );
      return response;
    },
    onSuccess: () => {
      toast({
        title: "Invoice approved",
        description: "The invoice has been approved and journal entries have been created.",
        variant: "success",
      });
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices", invoiceId] });
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices"] });
      queryClient.invalidateQueries({ queryKey: [orgId, "dashboard"] });
      queryClient.invalidateQueries({ queryKey: [orgId, "ledger"] });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to approve invoice",
        description: error.message || "An error occurred while approving the invoice.",
        variant: "error",
      });
    },
  });
}

// Void invoice
export function useVoidInvoice(orgId: string, invoiceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (reason: string) => {
      const response = await api.post<Invoice>(
        endpoints.invoices(orgId).void(invoiceId),
        { reason }
      );
      return response;
    },
    onSuccess: () => {
      toast({
        title: "Invoice voided",
        description: "The invoice has been voided and reversal entries have been created.",
        variant: "warning",
      });
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices", invoiceId] });
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices"] });
      queryClient.invalidateQueries({ queryKey: [orgId, "dashboard"] });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to void invoice",
        description: error.message || "An error occurred while voiding the invoice.",
        variant: "error",
      });
    },
  });
}

// Send invoice via email
export function useSendInvoice(orgId: string, invoiceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (emailData: { to: string; cc?: string; message?: string }) => {
      const response = await api.post<Invoice>(
        endpoints.invoices(orgId).send(invoiceId),
        emailData
      );
      return response;
    },
    onSuccess: () => {
      toast({
        title: "Invoice sent",
        description: "The invoice has been sent via email.",
        variant: "success",
      });
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices", invoiceId] });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to send invoice",
        description: error.message || "An error occurred while sending the invoice.",
        variant: "error",
      });
    },
  });
}

// Send via InvoiceNow (Peppol)
export function useSendInvoiceNow(orgId: string, invoiceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post<{
        status: string;
        message_id: string;
        transmission_log_id: string;
      }>(endpoints.invoices(orgId).sendInvoiceNow(invoiceId), {});
      return response;
    },
    onSuccess: () => {
      toast({
        title: "InvoiceNow transmission queued",
        description: "The invoice has been queued for InvoiceNow transmission. Check status for updates.",
        variant: "info",
      });
      queryClient.invalidateQueries({ queryKey: [orgId, "invoices", invoiceId] });
      queryClient.invalidateQueries({ queryKey: [orgId, "peppol"] });
    },
    onError: (error: Error) => {
      toast({
        title: "InvoiceNow transmission failed",
        description: error.message || "An error occurred while queuing the InvoiceNow transmission.",
        variant: "error",
      });
    },
  });
}

// InvoiceNow status response type
interface InvoiceNowStatusResponse {
  status: string;
  message_id?: string;
  transmitted_at?: string;
  delivered_at?: string;
  logs: Array<{
    id: string;
    status: string;
    timestamp: string;
    error_message?: string;
  }>;
}

// Get InvoiceNow status
export function useInvoiceNowStatus(orgId: string, invoiceId: string) {
  return useQuery<InvoiceNowStatusResponse>({
    queryKey: [orgId, "invoices", invoiceId, "invoicenow-status"],
    queryFn: async () => {
      const response = await api.get<InvoiceNowStatusResponse>(
        endpoints.invoices(orgId).invoiceNowStatus(invoiceId)
      );
      return response;
    },
    enabled: !!orgId && !!invoiceId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll every 5 seconds if pending
      if (data?.status === "PENDING" || data?.status === "TRANSMITTING") {
        return 5000;
      }
      return false;
    },
  });
}

// Download PDF
export function useInvoicePDF(orgId: string, invoiceId: string) {
  return useMutation({
    mutationFn: async () => {
      const url = `${endpoints.invoices(orgId).pdf(invoiceId)}`;
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("accessToken")}`,
        },
      });
      if (!response.ok) throw new Error("Failed to download PDF");
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `invoice-${invoiceId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    },
  });
}
