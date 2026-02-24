import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, endpoints } from "@/lib/api-client";

// Types matching backend schema
interface Contact {
  id: string;
  org_id: string;
  contact_type: "CUSTOMER" | "SUPPLIER" | "BOTH";
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
  address_line_1?: string;
  address_line_2?: string;
  postal_code?: string;
  country: string;
  uen?: string;
  gst_reg_number?: string;
  peppol_id?: string;
  is_peppol_enabled: boolean;
  payment_terms_days: number;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ContactInput {
  contact_type: "CUSTOMER" | "SUPPLIER" | "BOTH";
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
  address_line_1?: string;
  address_line_2?: string;
  postal_code?: string;
  country?: string;
  uen?: string;
  gst_reg_number?: string;
  peppol_id?: string;
  is_peppol_enabled?: boolean;
  payment_terms_days?: number;
  currency?: string;
}

// List contacts with optional filters
export function useContacts(
  orgId: string,
  filters?: {
    contact_type?: string;
    search?: string;
    is_active?: boolean;
  }
) {
  const queryString = filters
    ? "?" +
      new URLSearchParams(
        Object.entries(filters).filter(([, v]) => v !== undefined) as [string, string][]
      ).toString()
    : "";

  return useQuery({
    queryKey: [orgId, "contacts", filters],
    queryFn: async () => {
      const response = await api.get<{
        results: Contact[];
        count: number;
        next?: string;
        previous?: string;
      }>(endpoints.contacts(orgId).list + queryString);
      return response;
    },
    enabled: !!orgId,
  });
}

// Get single contact detail
export function useContact(orgId: string, contactId: string) {
  return useQuery({
    queryKey: [orgId, "contacts", contactId],
    queryFn: async () => {
      const response = await api.get<Contact>(
        endpoints.contacts(orgId).detail(contactId)
      );
      return response;
    },
    enabled: !!orgId && !!contactId,
  });
}

// Create contact
export function useCreateContact(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ContactInput) => {
      const response = await api.post<Contact>(
        endpoints.contacts(orgId).list,
        data
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [orgId, "contacts"] });
    },
  });
}

// Update contact
export function useUpdateContact(orgId: string, contactId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<ContactInput>) => {
      const response = await api.patch<Contact>(
        endpoints.contacts(orgId).detail(contactId),
        data
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [orgId, "contacts", contactId] });
      queryClient.invalidateQueries({ queryKey: [orgId, "contacts"] });
    },
  });
}

// Deactivate contact
export function useDeactivateContact(orgId: string, contactId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.delete<Contact>(
        endpoints.contacts(orgId).detail(contactId)
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [orgId, "contacts"] });
    },
  });
}
