# Milestone 5: Polish & Hardening — Execution Plan

## Overview
Final milestone focused on production readiness: testing infrastructure, security hardening, error resilience, and user experience polish.

---

## M5.1: Testing Infrastructure (Playwright)

### Objectives
- Set up Playwright E2E testing framework
- Create critical path test suite
- Configure test environment and fixtures

### Deliverables
| File | Purpose |
|------|---------|
| `playwright.config.ts` | Playwright configuration |
| `.github/workflows/e2e.yml` | CI workflow for E2E tests |
| `e2e/auth.spec.ts` | Authentication flow tests |
| `e2e/invoice.spec.ts` | Invoice creation flow tests |
| `e2e/dashboard.spec.ts` | Dashboard navigation tests |
| `e2e/fixtures.ts` | Test fixtures and helpers |

### Test Coverage
- [ ] Login flow (success/failure cases)
- [ ] Invoice creation with GST calculation
- [ ] Dashboard navigation and data display
- [ ] Responsive design verification
- [ ] Accessibility checks (axe-core)

---

## M5.2: Security Headers & Middleware

### Objectives
- Implement Next.js middleware for security headers
- Configure Content Security Policy
- Add HSTS and other security headers

### Deliverables
| File | Purpose |
|------|---------|
| `middleware.ts` | Next.js middleware with security headers |
| `lib/security.ts` | Security utility functions |

### Security Headers
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: [comprehensive CSP]
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

---

## M5.3: Error Boundaries & 404 Pages

### Objectives
- Create error boundary components
- Implement 404 not-found pages
- Add global error handling

### Deliverables
| File | Purpose |
|------|---------|
| `app/error.tsx` | Dashboard layout error boundary |
| `app/global-error.tsx` | Root error boundary |
| `app/not-found.tsx` | 404 page |
| `app/(dashboard)/error.tsx` | Dashboard-specific errors |
| `components/ui/error-boundary.tsx` | Reusable error boundary |

### Error UX
- Brutalist error design matching theme
- Retry functionality
- Error logging (Sentry-ready)
- User-friendly error messages

---

## M5.4: Loading States & Skeletons

### Objectives
- Create skeleton components matching design system
- Add loading.tsx for route segments
- Implement Suspense boundaries

### Deliverables
| File | Purpose |
|------|---------|
| `components/ui/skeleton.tsx` | Base skeleton component |
| `components/ui/skeleton-card.tsx` | Card skeleton |
| `components/ui/skeleton-table.tsx` | Table skeleton |
| `components/ui/skeleton-form.tsx` | Form skeleton |
| `app/(dashboard)/loading.tsx` | Dashboard loading state |
| `app/(dashboard)/invoices/loading.tsx` | Invoices loading state |
| `app/(dashboard)/ledger/loading.tsx` | Ledger loading state |

### Skeleton Design
- Dark theme matching "Illuminated Carbon"
- Animated pulse with accent-primary glow
- Square corners (consistent with design system)

---

## M5.5: Toast Notification System

### Objectives
- Integrate Radix Toast primitive
- Create toast provider and hook
- Add toast notifications for mutations

### Deliverables
| File | Purpose |
|------|---------|
| `components/ui/toast.tsx` | Toast primitive component |
| `components/ui/toaster.tsx` | Toast container |
| `hooks/use-toast.ts` | Toast hook |
| `providers/toast-provider.tsx` | Toast context provider |

### Toast Types
- Success (accent-primary)
- Error (alert/destructive)
- Warning (accent-secondary)
- Info (neutral)

### Integration Points
- Invoice creation success/error
- Login success/failure
- API error responses
- Form validation errors

---

## M5.6: Final Build & Verification

### Objectives
- Verify all builds pass
- Run linting
- Check TypeScript errors
- Verify static export works

### Verification Checklist
- [ ] `npm run build` succeeds
- [ ] `npm run lint` passes
- [ ] No TypeScript errors
- [ ] All routes render correctly
- [ ] Toast system functional
- [ ] Error boundaries working
- [ ] Loading states visible
- [ ] Security headers present

---

## Execution Order

```
Phase 1: Security Foundation
├── M5.2: Middleware + Security Headers
└── M5.3: Error Boundaries

Phase 2: UX Polish
├── M5.4: Loading States & Skeletons
├── M5.5: Toast Notification System
└── Update hooks with toast integration

Phase 3: Testing
├── M5.1: Playwright Setup
├── Create test fixtures
└── Write critical path tests

Phase 4: Verification
├── M5.6: Final Build & Verification
└── Update documentation
```

---

## Dependencies to Add

```json
{
  "devDependencies": {
    "@playwright/test": "^1.50.0",
    "@axe-core/playwright": "^4.10.0"
  }
}
```

(Radix Toast already in dependencies)

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Build Success | 100% |
| TypeScript Errors | 0 |
| Lint Errors | 0 |
| E2E Tests Passing | >80% critical paths |
| Security Headers | All present |
| WCAG Compliance | AAA maintained |
| Bundle Size | <300KB initial |

---

**Estimated Effort**: 4-6 hours
**Risk Level**: Low (non-breaking additions)
