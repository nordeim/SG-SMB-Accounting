/**
 * Server-Side API Client for LedgerSG
 * 
 * This module provides server-side only utilities for calling the backend API.
 * It handles JWT token refresh and authentication via HTTP-only cookies.
 * 
 * IMPORTANT: This module should ONLY be imported in Server Components
 * or server-side utilities (middleware, etc.). Never import in Client Components.
 */

import { cookies } from "next/headers";

// Backend API configuration
const API_BASE_URL = process.env.BACKEND_URL || "http://localhost:8000";

// Token refresh buffer (refresh if token expires in less than 5 minutes)
const TOKEN_REFRESH_BUFFER_MS = 5 * 60 * 1000;

interface TokenPayload {
  exp: number;
  user_id: string;
  [key: string]: unknown;
}

interface DashboardData {
  gst_payable: string;
  gst_payable_display: string;
  outstanding_receivables: string;
  outstanding_payables: string;
  revenue_mtd: string;
  revenue_ytd: string;
  cash_on_hand: string;
  gst_threshold_status: "SAFE" | "WARNING" | "CRITICAL" | "EXCEEDED";
  gst_threshold_utilization: number;
  gst_threshold_amount: string;
  gst_threshold_limit: string;
  compliance_alerts: ComplianceAlert[];
  invoices_pending: number;
  invoices_overdue: number;
  invoices_peppol_pending: number;
  current_gst_period: GSTPeriod;
  last_updated: string;
}

interface ComplianceAlert {
  id: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  title: string;
  message: string;
  action_required: string;
  deadline?: string;
  dismissed: boolean;
}

interface GSTPeriod {
  start_date: string;
  end_date: string;
  filing_due_date: string;
  days_remaining: number;
}

/**
 * Decode JWT payload without verification (for checking expiration)
 */
function decodeJwtPayload(token: string): TokenPayload | null {
  try {
    const payload = token.split(".")[1];
    const decoded = Buffer.from(payload, "base64url").toString("utf-8");
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

/**
 * Check if token needs refresh
 */
function needsRefresh(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload?.exp) return true;

  const expiresAt = payload.exp * 1000; // Convert to milliseconds
  return Date.now() + TOKEN_REFRESH_BUFFER_MS >= expiresAt;
}

/**
 * Refresh the access token using the refresh token
 */
async function refreshAccessToken(): Promise<string | null> {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get("refresh_token")?.value;

  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    // Note: In a real implementation, you would update the cookie here
    // However, Server Components cannot set cookies directly
    // This would need to be handled via a Server Action or middleware

    return data.access;
  } catch {
    return null;
  }
}

/**
 * Get valid access token (refresh if necessary)
 */
async function getValidAccessToken(): Promise<string | null> {
  const cookieStore = await cookies();
  let accessToken = cookieStore.get("access_token")?.value;

  if (!accessToken) {
    return null;
  }

  // Check if token needs refresh
  if (needsRefresh(accessToken)) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      accessToken = newToken;
    }
  }

  return accessToken;
}

/**
 * Server-side API fetch with authentication
 */
async function serverFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const accessToken = await getValidAccessToken();

  if (!accessToken) {
    throw new Error("Unauthorized");
  }

  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...options.headers,
    },
    // Ensure we don't cache auth-required requests
    cache: "no-store",
  });

  // Handle 401 by attempting token refresh once
  if (response.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      // Retry with new token
      return fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${newToken}`,
          ...options.headers,
        },
        cache: "no-store",
      });
    }
    throw new Error("Unauthorized");
  }

  return response;
}

/**
 * Fetch dashboard data for an organization
 * 
 * This function is designed to be called from Server Components only.
 */
export async function fetchDashboardData(
  orgId: string
): Promise<DashboardData> {
  const response = await serverFetch(`/api/v1/${orgId}/dashboard/`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: "Unknown error" },
    }));
    throw new Error(error.error?.message || "Failed to fetch dashboard data");
  }

  return response.json();
}

/**
 * Check if user is authenticated (server-side)
 */
export async function isAuthenticated(): Promise<boolean> {
  const token = await getValidAccessToken();
  return token !== null;
}

/**
 * Get current user ID from token (server-side)
 */
export async function getCurrentUserId(): Promise<string | null> {
  const token = await getValidAccessToken();
  if (!token) return null;

  const payload = decodeJwtPayload(token);
  return payload?.user_id || null;
}

// Export types
export type {
  DashboardData,
  ComplianceAlert,
  GSTPeriod,
  TokenPayload,
};
