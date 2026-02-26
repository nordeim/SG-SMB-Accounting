/**
 * LEDGERSG API CLIENT
 * 
 * Purpose: Typed fetch wrapper with error handling, retry logic, JWT refresh
 * All API calls flow through this client for consistency
 * 
 * Backend: Django 6.0 + DRF with JWT Authentication
 * - Access token: 15 min expiry, stored in memory
 * - Refresh token: 7 day expiry, HttpOnly cookie
 * - Org-scoped URLs: /api/v1/{org_id}/invoices/
 */

import { QueryClient, type QueryFunction } from "@tanstack/react-query";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Custom error class for API errors
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public errors?: Record<string, string[]>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Token management
let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function clearAuth() {
  accessToken = null;
}

// Base request function
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Add auth header if token exists
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Important for HttpOnly refresh cookie
  });

  // Handle 401 - try to refresh token
  if (response.status === 401 && accessToken) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // Retry the original request with new token
      headers["Authorization"] = `Bearer ${accessToken}`;
      const retryResponse = await fetch(url, {
        ...options,
        headers,
        credentials: "include",
      });
      return handleResponse<T>(retryResponse);
    } else {
      // Refresh failed, clear auth
      clearAuth();
      window.location.href = "/login";
      throw new ApiError(401, "Session expired. Please log in again.");
    }
  }

  return handleResponse<T>(response);
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.message || errorData.detail || `Request failed: ${response.statusText}`,
      errorData.errors
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

async function tryRefreshToken(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });

    if (response.ok) {
      const data = await response.json();
      setAccessToken(data.access);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

// HTTP method helpers
export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint, { method: "GET" }),
  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),
  put: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  patch: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: "DELETE" }),
};

// API Endpoints
export const endpoints = {
  // Authentication
  auth: {
    login: "/api/v1/auth/login/",
    logout: "/api/v1/auth/logout/",
    refresh: "/api/v1/auth/refresh/",
    me: "/api/v1/auth/me/",
    changePassword: "/api/v1/auth/change-password/",
  },

  // Organisations
  organisations: {
    list: "/api/v1/organisations/",
    detail: (id: string) => `/api/v1/${id}/`,
    settings: (id: string) => `/api/v1/${id}/settings/`,
  },

  // Invoices (org-scoped) - Aligned with backend: /invoicing/documents/
  invoices: (orgId: string) => ({
    list: `/api/v1/${orgId}/invoicing/documents/`,
    detail: (id: string) => `/api/v1/${orgId}/invoicing/documents/${id}/`,
    // Phase 2: These endpoints will be implemented in the backend
    approve: (id: string) => `/api/v1/${orgId}/invoicing/documents/${id}/approve/`,
    void: (id: string) => `/api/v1/${orgId}/invoicing/documents/${id}/void/`,
    pdf: (id: string) => `/api/v1/${orgId}/invoicing/documents/${id}/pdf/`,
    send: (id: string) => `/api/v1/${orgId}/invoicing/documents/${id}/send/`,
    sendInvoiceNow: (id: string) => `/api/v1/${orgId}/invoicing/documents/${id}/send-invoicenow/`,
    invoiceNowStatus: (id: string) => `/api/v1/${orgId}/invoicing/documents/${id}/invoicenow-status/`,
  }),

  // Contacts (org-scoped) - Aligned with backend: /invoicing/contacts/
  contacts: (orgId: string) => ({
    list: `/api/v1/${orgId}/invoicing/contacts/`,
    detail: (id: string) => `/api/v1/${orgId}/invoicing/contacts/${id}/`,
  }),

  // Dashboard (org-scoped)
  dashboard: (orgId: string) => ({
    metrics: `/api/v1/${orgId}/dashboard/metrics/`,
    alerts: `/api/v1/${orgId}/dashboard/alerts/`,
  }),

  // Banking (org-scoped)
  banking: (orgId: string) => ({
    accounts: `/api/v1/${orgId}/bank-accounts/`,
    payments: `/api/v1/${orgId}/payments/`,
    receivePayment: `/api/v1/${orgId}/payments/receive/`,
    makePayment: `/api/v1/${orgId}/payments/make/`,
  }),

  // Chart of Accounts (org-scoped)
  accounts: (orgId: string) => ({
    list: `/api/v1/${orgId}/accounts/`,
    detail: (id: string) => `/api/v1/${orgId}/accounts/${id}/`,
    types: `/api/v1/${orgId}/accounts/types/`,
  }),

  // Fiscal (org-scoped)
  fiscal: (orgId: string) => ({
    years: `/api/v1/${orgId}/fiscal-years/`,
    periods: `/api/v1/${orgId}/fiscal-periods/`,
    closeYear: (id: string) => `/api/v1/${orgId}/fiscal-years/${id}/close/`,
    closePeriod: (id: string) => `/api/v1/${orgId}/fiscal-periods/${id}/close/`,
  }),

  // Peppol
  peppol: (orgId: string) => ({
    transmissionLog: `/api/v1/${orgId}/peppol/transmission-log/`,
    settings: `/api/v1/${orgId}/peppol/settings/`,
  }),
};

// TanStack Query Client Configuration
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry on 401/403
        if (error instanceof ApiError) {
          if (error.status === 401 || error.status === 403) {
            return false;
          }
        }
        return failureCount < 2;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
      onError: (error: unknown) => {
        // Global error handling
        if (error instanceof ApiError) {
          console.error("API Error:", error.message);
        }
      },
    },
  },
});

// Type-safe query hooks factory
export function createQueryHooks<T>(
  key: string,
  fetcher: QueryFunction<T>
) {
  return {
    key: [key],
    fetcher,
  };
}
