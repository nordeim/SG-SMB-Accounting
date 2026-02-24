"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { api, endpoints, setAccessToken, clearAuth } from "@/lib/api-client";
import { queryClient } from "@/lib/api-client";

// Types matching backend schema
interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  is_active: boolean;
  last_login_at?: string;
}

interface Organisation {
  id: string;
  name: string;
  legal_name?: string;
  uen?: string;
  entity_type: string;
  gst_registered: boolean;
  gst_reg_number?: string;
  gst_reg_date?: string;
  gst_scheme: string;
  gst_filing_frequency: string;
  peppol_participant_id?: string;
  invoicenow_enabled: boolean;
  fy_start_month: number;
  base_currency: string;
  timezone: string;
  is_active: boolean;
}

interface UserOrganisation {
  id: string;
  org: Organisation;
  role: {
    id: string;
    name: string;
    can_manage_org: boolean;
    can_manage_users: boolean;
    can_manage_coa: boolean;
    can_create_invoices: boolean;
    can_approve_invoices: boolean;
    can_void_invoices: boolean;
    can_create_journals: boolean;
    can_manage_banking: boolean;
    can_file_gst: boolean;
    can_view_reports: boolean;
    can_export_data: boolean;
  };
  is_default: boolean;
}

interface AuthContextType {
  user: User | null;
  organisations: UserOrganisation[];
  currentOrg: Organisation | null;
  currentRole: UserOrganisation["role"] | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  switchOrg: (orgId: string) => void;
  hasPermission: (permission: keyof UserOrganisation["role"]) => boolean;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [organisations, setOrganisations] = React.useState<UserOrganisation[]>([]);
  const [currentOrgId, setCurrentOrgId] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const router = useRouter();

  // Derived state
  const currentOrg = React.useMemo(() => {
    if (!currentOrgId) return null;
    const userOrg = organisations.find((uo) => uo.org.id === currentOrgId);
    return userOrg?.org || null;
  }, [currentOrgId, organisations]);

  const currentRole = React.useMemo(() => {
    if (!currentOrgId) return null;
    const userOrg = organisations.find((uo) => uo.org.id === currentOrgId);
    return userOrg?.role || null;
  }, [currentOrgId, organisations]);

  const isAuthenticated = !!user;

  // Check for existing session on mount
  React.useEffect(() => {
    async function checkSession() {
      try {
        // Try to get current user - this will fail if no valid refresh token
        const userData = await api.get<User>(endpoints.auth.me);
        setUser(userData);
        
        // Fetch user's organisations
        const orgsData = await api.get<{ results: UserOrganisation[] }>(
          endpoints.organisations.list
        );
        setOrganisations(orgsData.results);
        
        // Set default org
        const defaultOrg = orgsData.results.find((uo) => uo.is_default);
        if (defaultOrg) {
          setCurrentOrgId(defaultOrg.org.id);
        } else if (orgsData.results.length > 0) {
          setCurrentOrgId(orgsData.results[0].org.id);
        }
      } catch {
        // No valid session
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    }

    checkSession();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.post<{
      user: User;
      organisations: UserOrganisation[];
      access: string;
    }>(endpoints.auth.login, { email, password });

    setAccessToken(response.access);
    setUser(response.user);
    setOrganisations(response.organisations);

    // Set default org
    const defaultOrg = response.organisations.find((uo) => uo.is_default);
    if (defaultOrg) {
      setCurrentOrgId(defaultOrg.org.id);
    } else if (response.organisations.length > 0) {
      setCurrentOrgId(response.organisations[0].org.id);
    }

    // Invalidate any cached queries
    queryClient.invalidateQueries();
  };

  const logout = async () => {
    try {
      await api.post(endpoints.auth.logout);
    } catch {
      // Ignore logout errors
    } finally {
      clearAuth();
      setUser(null);
      setOrganisations([]);
      setCurrentOrgId(null);
      queryClient.clear();
      router.push("/login");
    }
  };

  const switchOrg = (orgId: string) => {
    const org = organisations.find((uo) => uo.org.id === orgId);
    if (org) {
      setCurrentOrgId(orgId);
      // Invalidate org-scoped queries
      queryClient.invalidateQueries({ queryKey: [orgId] });
    }
  };

  const hasPermission = (permission: keyof UserOrganisation["role"]): boolean => {
    if (!currentRole) return false;
    return currentRole[permission] === true;
  };

  const value: AuthContextType = {
    user,
    organisations,
    currentOrg,
    currentRole,
    isLoading,
    isAuthenticated,
    login,
    logout,
    switchOrg,
    hasPermission,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// Hook for org-scoped API calls
export function useCurrentOrg() {
  const { currentOrg, switchOrg, hasPermission } = useAuth();
  
  if (!currentOrg) {
    throw new Error("No current organisation selected");
  }

  return {
    orgId: currentOrg.id,
    org: currentOrg,
    switchOrg,
    hasPermission,
  };
}
