• Analysis Complete: The frontend is using HARDCODED MOCK data, not the backend API.

  Current State

  Frontend (Mock Data):

  // page.tsx line 21
  const data = createMockDashboardMetrics();  // Returns static values like:
  // gst_payable_display: "12,450.00"
  // outstanding_receivables: "45,230.50"
  // revenue_ytd: "1,450,000.00"

  Backend (Real API Available): The backend HAS a real summary endpoint at:

  GET /api/v1/{org_id}/summary/  → OrganisationSummaryView

  This returns:

  • Organisation details
  • Current fiscal year
  • Open periods count
  • Account counts (total/active)
  • Member count

  The Problem

  The dashboard was converted to a Server Component (for performance), but it imports mock data directly instead of fetching from the backend API. The values you see in the browser are:

   Displayed Value     Source                         Real?
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   S$ 12,450.00        createMockDashboardMetrics()   ❌ MOCK
   S$ 45,230.50        createMockDashboardMetrics()   ❌ MOCK
   S$ 1,450,000.00     createMockDashboardMetrics()   ❌ MOCK
   78% GST Threshold   createMockDashboardMetrics()   ❌ MOCK

  Solution Options

  Option 1: Convert Dashboard to Client Component with API Fetching

  • Use useEffect + fetch to call backend
  • Requires authentication token handling
  • Shows loading states during data fetch

  Option 2: Keep Server Component, Add Server-Side Fetch

  • Use Next.js fetch() with cache: 'no-store'
  • Requires passing auth cookies to backend
  • More complex with JWT authentication

  Option 3: Create a New Dashboard API Endpoint

  • Build a comprehensive /dashboard endpoint in backend
  • Aggregates all metrics in one call
  • Frontend calls this single endpoint

  Which approach would you prefer? The backend has the data, but the frontend isn't connected to it yet.

---

• Security & Best Practices Analysis

From a security-first perspective, Option 2 (Server Component with Server-Side Fetch) combined with Option 3 (Dedicated Dashboard API) is the optimal approach.

Why Server Components Win on Security

 Aspect               Client Component (Option 1)           Server Component (Option 2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Token Exposure       ❌ JWT in browser memory (XSS risk)   ✅ Token stays on server
 Credential Storage   ❌ localStorage/sessionStorage        ✅ HTTP-only cookies
 API Keys             ❌ Exposed to client                  ✅ Server-side only
 Data Exposure        ❌ All data sent to browser           ✅ Only rendered HTML
 Request Origin       ❌ Public IP (spoofable)              ✅ Internal/private network

Recommended Architecture

┌─────────────────────────────────────────────────────────────┐
│                      BROWSER                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Server Component (DashboardPage)                   │   │
│  │  • No JavaScript sent to client                     │   │
│  │  • Renders HTML server-side                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              NEXT.JS SERVER (Node.js)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Auth Middleware                                    │   │
│  │  • Reads HTTP-only cookie                           │   │
│  │  • Validates JWT                                    │   │
│  │  • Refreshes token if needed                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Server-Side Fetch                                  │   │
│  │  • Internal call to backend:8000                    │   │
│  │  • Passes JWT in Authorization header               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              DJANGO BACKEND (localhost:8000)                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  GET /api/v1/{org_id}/dashboard/                    │   │
│  │  • Aggregates all metrics                           │   │
│  │  • Returns JSON                                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

Implementation Plan

Step 1: Secure Auth with HTTP-Only Cookies

// middleware.ts - Validate session server-side
export async function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  if (!token) return redirect('/login');
  // Validate with backend, refresh if needed
}

Step 2: Create Dashboard API Endpoint (Backend)

# Backend: GET /api/v1/{org_id}/dashboard/
# Aggregates: GST metrics, invoices, cash, alerts, threshold
# Single call returns all dashboard data

Step 3: Server Component Fetches Data

// Server Component - NO "use client"
export default async function DashboardPage() {
  const data = await fetchDashboardData(); // Server-side only
  return <DashboardUI data={data} />;
}

Why This is Optimal

1. Zero JWT Exposure: Tokens never reach browser JavaScript
2. XSS Protection: Even if XSS occurs, attacker can't steal tokens
3. Automatic Token Refresh: Server handles 401 → refresh → retry
4. No Loading States: HTML rendered server-side, instant display
5. Defense in Depth: Backend still validates every request
6. Performance: Server-to-server is faster than client → API

Trade-offs

• Complexity: Higher initial setup
• Server Load: More work on Next.js server
• Real-time Updates: Need Server Actions or revalidation for live data

Verdict: Option 2 + Option 3 is the enterprise-grade, security-compliant approach. It aligns with Next.js 13+ App Router best practices and keeps credentials secure.

---

• ✅ TDD Implementation Complete!

Summary

All 22 Tests Passing:

 Component           Tests   Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DashboardService    12      ✅ All Pass
 DashboardView API   10      ✅ All Pass

Files Created/Modified

Backend (TDD - Phase 1):

apps/backend/
├── apps/core/services/dashboard_service.py      # NEW: Aggregates dashboard data
├── apps/core/views/dashboard.py                 # NEW: API endpoint
├── apps/core/urls/__init__.py                   # MODIFIED: Added /dashboard/ route
├── apps/core/tests/
│   ├── test_dashboard_service.py               # NEW: 12 service tests
│   └── test_dashboard_view.py                  # NEW: 10 API tests
└── apps/core/models/invoice_document.py        # FIXED: Model-schema alignment

Frontend (Phases 2 & 3):

apps/web/
├── src/lib/server/api-client.ts                # NEW: Server-side auth & API client
└── src/app/(dashboard)/dashboard/page.tsx      # MODIFIED: Async Server Component

Key Features Implemented

1. Backend Dashboard API (GET /api/v1/{org_id}/dashboard/)
  • GST payable calculation (output - input tax)
  • Cash on hand tracking
  • Outstanding receivables/payables
  • MTD/YTD revenue calculations
  • GST threshold monitoring (IRAS compliance)
  • Compliance alerts (filing deadlines, overdue invoices)
  • Invoice statistics (pending, overdue, peppol)
2. Security-First Frontend
  • Server Components only (no JWT in browser)
  • HTTP-only cookie authentication
  • Automatic token refresh
  • Server-side data fetching
3. TDD Approach
  • Red: Wrote 22 tests first
  • Green: Implemented code to pass tests
  • All tests passing ✅

API Response Format

{
  "gst_payable": "3300.0000",
  "gst_payable_display": "3,300.00",
  "outstanding_receivables": "50,500.00",
  "cash_on_hand": "145,000.00",
  "revenue_mtd": "12,500.00",
  "revenue_ytd": "145,000.00",
  "gst_threshold_status": "WARNING",
  "gst_threshold_utilization": 78,
  "compliance_alerts": [...],
  "invoices_pending": 5,
  "invoices_overdue": 3,
  "current_gst_period": {...},
  "last_updated": "2026-02-28T10:15:30.123456"
}

The browser will now display real data from the backend instead of static mock values!


