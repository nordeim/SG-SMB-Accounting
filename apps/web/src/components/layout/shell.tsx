"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Menu,
  X,
  LayoutDashboard,
  FileText,
  PieChart,
  Settings,
  BookOpen,
  Receipt,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";

/*
 * BRUTALIST LAYOUT SHELL
 * - Asymmetric grid ready
 * - Collapsible sidebar (mobile)
 * - Sticky header with blur backdrop
 */

interface ShellProps {
  children: React.ReactNode;
}

interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
}

const navItems: NavItem[] = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: FileText, label: "Invoices", href: "/invoices" },
  { icon: Receipt, label: "Quotes", href: "/quotes" },
  { icon: BookOpen, label: "Ledger", href: "/ledger" },
  { icon: PieChart, label: "Reports", href: "/reports" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

export function Shell({ children }: ShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  const isActiveRoute = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/dashboard" || pathname === "/";
    }
    return pathname?.startsWith(href);
  };

  return (
    <div className="min-h-screen bg-void text-text-primary flex">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-void/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed md:sticky top-0 h-screen w-64 bg-carbon border-r border-border z-50",
          "transition-transform duration-300 ease-in-out",
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Logo Section */}
        <div className="p-6 border-b border-border">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-accent-primary flex items-center justify-center rounded-sm">
              <span className="font-mono font-bold text-void text-lg">L</span>
            </div>
            <h1 className="font-display text-xl font-bold tracking-tight">
              LEDGER<span className="text-accent-primary">SG</span>
            </h1>
          </Link>
          <p className="text-xs text-text-muted mt-1 font-mono">
            IRAS-Compliant Accounting
          </p>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1" aria-label="Main navigation">
          {navItems.map((item) => {
            const isActive = isActiveRoute(item.href);
            return (
              <Link
                key={item.label}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 text-sm font-medium transition-colors rounded-sm",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/50",
                  isActive
                    ? "bg-surface text-accent-primary border-l-2 border-accent-primary"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <item.icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.label}</span>
                {isActive && (
                  <ChevronRight className="h-4 w-4 ml-auto" aria-hidden="true" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer Info */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-surface rounded-sm flex items-center justify-center">
              <span className="text-xs font-mono text-text-secondary">DU</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                Demo User
              </p>
              <p className="text-xs text-text-muted font-mono truncate">
                ORG-001
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-void/90 backdrop-blur supports-[backdrop-filter]:bg-void/80 px-4 md:px-6">
          {/* Mobile Menu Toggle */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden h-9 w-9"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label={sidebarOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={sidebarOpen}
            aria-controls="main-navigation"
          >
            {sidebarOpen ? (
              <X className="h-5 w-5" aria-hidden="true" />
            ) : (
              <Menu className="h-5 w-5" aria-hidden="true" />
            )}
          </Button>

          {/* Breadcrumb / Page Title */}
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-display font-semibold text-text-primary truncate">
              {navItems.find((item) => isActiveRoute(item.href))?.label ||
                "LedgerSG"}
            </h2>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="hidden sm:flex rounded-sm border-border text-text-secondary"
            >
              <Receipt className="h-4 w-4 mr-2" />
              New Invoice
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
