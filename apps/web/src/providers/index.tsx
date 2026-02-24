"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/api-client";
import { AuthProvider } from "./auth-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}

export { useAuth, useCurrentOrg } from "./auth-provider";
