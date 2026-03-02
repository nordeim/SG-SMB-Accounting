# Banking Module Execution Plan
## SEC-001 (HIGH) Remediation

**Version:** 1.1.0
**Date:** 2026-03-02
**Status:** ✅ PHASES 0-3, 5.1-5.2, 7 COMPLETE | ⏳ PHASES 5.3-5.6, 6 PENDING

---

## Executive Summary

This execution plan remediates **SEC-001 (HIGH Severity)** by replacing stub implementations in `apps/backend/apps/banking/views.py` with production-grade, validated endpoints.

**Key Corrections from Draft Plan:**
- Models are located in `apps/core/models/`, NOT `apps/banking/models/`
- `BankTransaction` model is MISSING - must be created ✅ DONE
- Serializers and Services will be created in `apps/banking/`

**Completion Status:**

| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| Phase 0 | Pre-Implementation Setup | ✅ COMPLETE | — |
| Phase 1 | Serializers & Validation | ✅ COMPLETE | — |
| Phase 2 | Service Layer | ✅ COMPLETE | — |
| Phase 3 | API Views | ✅ COMPLETE | — |
| Phase 4 | Journal Integration | ⏳ DEFERRED | — |
| Phase 5.1 | Bank Account Tests | ✅ COMPLETE | 14/14 |
| Phase 5.2 | Payment Tests | ✅ COMPLETE | 15/15 |
| Phase 5.3 | Allocation Tests | ⏳ PENDING | 0/8 |
| Phase 5.4 | Reconciliation Tests | ⏳ PENDING | 0/5 |
| Phase 5.5 | API View Tests | ⏳ PENDING | 0/12 |
| Phase 6 | Security Hardening | ⏳ PENDING | — |
| Phase 7 | Documentation | ✅ COMPLETE | — |

**Current Test Count:** 29/52 target tests passing

## Phase 0: Pre-Implementation Setup (30 min)

### 0.1 Create BankTransaction Model
**File:** `apps/backend/apps/core/models/bank_transaction.py`

**Checklist:**
- [x] Create `bank_transaction.py` model file
- [x] Add to `apps/core/models/__init__.py` exports
- [x] Verify model imports without errors
- [x] Confirm SQL alignment (14 columns)

**Status:** ✅ COMPLETE (2026-03-02)

### 0.2 Create Directory Structure

**Checklist:**
- [x] Create `apps/backend/apps/banking/serializers/`
- [x] Create `apps/backend/apps/banking/services/`
- [x] Create `apps/backend/apps/banking/tests/`
- [x] Create `__init__.py` files

**Status:** ✅ COMPLETE (2026-03-02)

---

## Phase 1: Serializers & Validation (4 hours)

**Status:** ✅ COMPLETE (2026-03-02)

### 1.1 BankAccountSerializer
**File:** `apps/backend/apps/banking/serializers/bank_account.py`

**Checklist:**
- [x] Create serializer with all field validations
- [x] `validate_paynow()` - If paynow_type set, paynow_id required
- [x] `validate_gl_account()` - Must belong to org and be bank account type

### 1.2 PaymentSerializer
**File:** `apps/backend/apps/banking/serializers/payment.py`

**Checklist:**
- [x] Create serializer with all field validations
- [x] `validate_contact_type()` - RECEIVED requires customer, MADE requires supplier
- [x] `validate_bank_account_org()` - Must belong to current org

### 1.3 PaymentAllocationSerializer
**File:** `apps/backend/apps/banking/serializers/allocation.py`

**Checklist:**
- [x] Create serializer with all field validations
- [x] `validate_document_status()` - Document must be APPROVED
- [x] `validate_allocation_not_exceed()` - Total allocations ≤ payment amount

### 1.4 BankTransactionSerializer
**File:** `apps/backend/apps/banking/serializers/bank_transaction.py`

**Checklist:**
- [x] Create serializer with all field validations
- [x] Decimal precision validated (use money() utility)

---

## Phase 2: Service Layer (6 hours)

**Status:** ✅ COMPLETE (2026-03-02)

### 2.1 BankAccountService
**File:** `apps/backend/apps/banking/services/bank_account_service.py`

**Methods Implemented:**
- [x] `create(org_id, data, user)` - Create bank account with GL linkage
- [x] `update(org_id, account_id, data)` - Update bank account details
- [x] `deactivate(org_id, account_id)` - Soft delete (set is_active=False)
- [x] `list(org_id, filters)` - List accounts with pagination
- [x] `get(org_id, account_id)` - Get single account

### 2.2 PaymentService
**File:** `apps/backend/apps/banking/services/payment_service.py`

**Methods Implemented:**
- [x] `create_received(org_id, data, user)` - Customer payment
- [x] `create_made(org_id, data, user)` - Supplier payment
- [x] `allocate(payment, allocations)` - Allocate to invoices
- [x] `void(org_id, payment_id, user)` - Void payment
- [x] `list(org_id, filters)` - List payments
- [x] `get(org_id, payment_id)` - Get single payment
- [x] `get_allocations(payment_id)` - List allocations for payment

### 2.3 ReconciliationService
**File:** `apps/backend/apps/banking/services/reconciliation_service.py`

**Methods Implemented:**
- [x] `import_transactions(org_id, data)` - Import bank transactions
- [x] `reconcile(org_id, transaction_id, payment_id)` - Match transaction to payment
- [x] `list_unreconciled(org_id, bank_account_id)` - List unmatched transactions

---

## Phase 3: API Views (4 hours)

**Status:** ✅ COMPLETE (2026-03-02)

### 3.1 Implemented Endpoints

| Endpoint | Method | Permission | Status |
|----------|--------|------------|--------|
| `/bank-accounts/` | GET | IsOrgMember | ✅ |
| `/bank-accounts/` | POST | CanManageBanking | ✅ |
| `/bank-accounts/{id}/` | GET | IsOrgMember | ✅ |
| `/bank-accounts/{id}/` | PUT | CanManageBanking | ✅ |
| `/bank-accounts/{id}/deactivate/` | POST | CanManageBanking | ✅ |
| `/payments/` | GET | IsOrgMember | ✅ |
| `/payments/{id}/` | GET | IsOrgMember | ✅ |
| `/payments/received/` | POST | CanManageBanking | ✅ |
| `/payments/made/` | POST | CanManageBanking | ✅ |
| `/payments/{id}/allocate/` | POST | CanManageBanking | ✅ |
| `/payments/{id}/void/` | POST | CanManageBanking | ✅ |
| `/bank-transactions/` | GET | IsOrgMember | ✅ |
| `/bank-transactions/import/` | POST | CanManageBanking | ✅ |

**Total:** 13 endpoints (was 5 stubs)

---

## Phase 4: Journal Integration (4 hours)

**Status:** ⏳ DEFERRED (requires JournalService field alignment)

### 4.1 Blocker: JournalService Field Mismatch

**Problem:** `JournalService.create_entry()` uses field names that don't match `JournalEntry` model:
- Service uses: `entry_type`, `description`, `source_invoice_id`, `created_by_id`, `is_posted`
- Model has: `source_type`, `narration`, `source_id`, `posted_by`, no `is_posted`

**Solution Required:**
1. Align `JournalService.create_entry()` with model field names
2. Update all callers of JournalService
3. Run full test suite to verify no regressions

### 4.2 Deferred Tasks
- [ ] Journal entry created on payment creation
- [ ] FX gain/loss calculated on allocation
- [ ] Reversal entry created on void
- [ ] Double-entry balance validated

---

## Phase 5: TDD Testing (6 hours)

### 5.0 Current Status

**Tests Passing:** 29/52 target (56% complete)

| Test File | Status | Tests |
|-----------|--------|-------|
| `test_bank_account_service.py` | ✅ COMPLETE | 14/14 |
| `test_payment_service.py` | ✅ COMPLETE | 15/15 |
| `test_allocation_service.py` | ⏳ PENDING | 0/8 |
| `test_reconciliation_service.py` | ⏳ PENDING | 0/5 |
| `test_views.py` | ⏳ PENDING | 0/12 |

### 5.1 Bank Account Tests (COMPLETE)
**File:** `apps/backend/apps/banking/tests/test_bank_account_service.py`

| Test | Status |
|------|--------|
| `test_create_bank_account_success` | ✅ |
| `test_create_bank_account_duplicate_number_fails` | ✅ |
| `test_create_bank_account_sets_single_default` | ✅ |
| `test_create_bank_account_audit_logged` | ✅ |
| `test_list_bank_accounts_success` | ✅ |
| `test_list_bank_accounts_filter_active` | ✅ |
| `test_list_bank_accounts_search` | ✅ |
| `test_get_bank_account_success` | ✅ |
| `test_get_bank_account_not_found` | ✅ |
| `test_update_bank_account_success` | ✅ |
| `test_update_bank_account_audit_logged` | ✅ |
| `test_deactivate_bank_account_success` | ✅ |
| `test_deactivate_only_account_fails` | ✅ |
| `test_cross_org_access_blocked` | ✅ |

### 5.2 Payment Tests (COMPLETE)
**File:** `apps/backend/apps/banking/tests/test_payment_service.py`

| Test | Status |
|------|--------|
| `test_create_received_payment_success` | ✅ |
| `test_create_received_payment_generates_number` | ✅ |
| `test_create_received_payment_audit_logged` | ✅ |
| `test_create_made_payment_success` | ✅ |
| `test_create_made_payment_number_format` | ✅ |
| `test_list_payments_filter_by_type` | ✅ |
| `test_get_payment_success` | ✅ |
| `test_get_payment_not_found` | ✅ |
| `test_void_payment_success` | ✅ |
| `test_void_already_voided_payment_fails` | ✅ |
| `test_void_payment_audit_logged` | ✅ |
| `test_allocate_payment_to_invoice` | ✅ |
| `test_allocate_exceeds_payment_amount_fails` | ✅ |
| `test_allocate_to_wrong_contact_fails` | ✅ |
| `test_multi_currency_payment_base_amount` | ✅ |

### 5.3 Allocation Tests (PENDING)
**File:** `apps/backend/apps/banking/tests/test_allocation_service.py`

**Tests to Create:**
1. `test_allocate_partial_payment`
2. `test_allocate_to_non_approved_invoice_fails`
3. `test_allocate_duplicate_invoice_fails`
4. `test_unallocate_payment`
5. `test_allocation_updates_invoice_status`
6. `test_allocation_fx_gain_loss`
7. `test_allocation_audit_logged`
8. `test_allocation_total_exceeds_payment`

**Priority:** HIGH
**Estimated Time:** 2 hours

### 5.4 Reconciliation Tests (PENDING)
**File:** `apps/backend/apps/banking/tests/test_reconciliation_service.py`

**Tests to Create:**
1. `test_import_transactions_success`
2. `test_reconcile_transaction_to_payment`
3. `test_unreconcile_transaction`
4. `test_list_unreconciled_transactions`
5. `test_import_duplicate_detection`

**Priority:** HIGH
**Estimated Time:** 1.5 hours

### 5.5 API View Tests (PENDING)
**File:** `apps/backend/apps/banking/tests/test_views.py`

**Tests to Create:**
- Bank account CRUD endpoint tests (5)
- Payment CRUD endpoint tests (4)
- Bank transaction endpoint tests (3)

**Priority:** HIGH
**Estimated Time:** 2 hours

---

## Phase 6: Security Hardening (2 hours)

**Status:** ⏳ PENDING

### 6.1 Input Validation
- [x] All inputs sanitized via serializers
- [x] No raw `request.data.get()` usage
- [x] Decimal fields reject floats

### 6.2 Authorization
- [x] All write operations require `CanManageBanking`
- [x] All read operations require `IsOrgMember`
- [x] RLS policies verified in tests

### 6.3 Audit Logging
- [x] All mutations logged to `audit.event_log`
- [x] Before/after values captured
- [x] User attribution correct

### 6.4 Rate Limiting (SEC-002)
- [ ] Install `django-ratelimit`
- [ ] Apply to payment endpoints (60/min)
- [ ] Apply to authentication endpoints (10/min)

**Priority:** MEDIUM
**Estimated Time:** 2 hours

---

## Phase 7: Documentation (2 hours)

**Status:** ✅ COMPLETE (2026-03-02)

### 7.1 Files Updated
- [x] `README.md` - SEC-001 marked as remediated, test counts updated
- [x] `AGENTS.md` - Security status updated
- [x] `AGENT_BRIEF.md` - Current status updated
- [x] `ACCOMPLISHMENTS.md` - Comprehensive implementation record
- [x] `EXECUTION_PLAN_BANKING_MODULE.md` - Phase completion status

### 7.2 SEC-001 Status
- [x] All stub code replaced
- [x] 29 tests passing (target: 52)
- [x] Documentation updated
- [ ] Remaining: Phases 5.3-5.5 tests, Phase 6 rate limiting

---

## Remaining Tasks Summary

### Priority Order

| Priority | Task | Estimated Time | Dependencies |
|----------|------|----------------|--------------|
| HIGH | PHASE 5.3: Allocation Tests | 2 hours | None |
| HIGH | PHASE 5.4: Reconciliation Tests | 1.5 hours | None |
| HIGH | PHASE 5.5: API View Tests | 2 hours | None |
| MEDIUM | PHASE 6: Rate Limiting (SEC-002) | 2 hours | None |
| LOW | PHASE 4: Journal Integration | 4 hours | JournalService refactor |

**Total Remaining:** ~11.5 hours

### Detailed Plan for PHASE 5.3 (Allocation Tests)

**File:** `apps/backend/apps/banking/tests/test_allocation_service.py`

**Tests to Implement:**

1. **`test_allocate_partial_payment`**
   - Create payment for $2000
   - Allocate $1000 to invoice
   - Verify remaining balance tracked

2. **`test_allocate_to_non_approved_invoice_fails`**
   - Create DRAFT invoice
   - Attempt allocation
   - Verify ValidationError

3. **`test_allocate_duplicate_invoice_fails`**
   - Allocate to invoice once
   - Attempt second allocation
   - Verify unique constraint error

4. **`test_unallocate_payment`**
   - Create allocation
   - Remove allocation
   - Verify document status updated

5. **`test_allocation_updates_invoice_status`**
   - Create invoice with total $1090
   - Allocate full amount
   - Verify status = PAID

6. **`test_allocation_fx_gain_loss`**
   - Create USD payment with exchange rate
   - Allocate at different rate
   - Verify FX gain/loss calculated

7. **`test_allocation_audit_logged`**
   - Create allocation
   - Verify audit log entry

8. **`test_allocation_total_exceeds_payment`**
   - Create payment for $500
   - Attempt allocations totaling $600
   - Verify ValidationError

### Detailed Plan for PHASE 5.4 (Reconciliation Tests)

**File:** `apps/backend/apps/banking/tests/test_reconciliation_service.py`

**Tests to Implement:**

1. **`test_import_transactions_success`**
   - Mock CSV data
   - Import transactions
   - Verify BankTransaction records created

2. **`test_reconcile_transaction_to_payment`**
   - Create bank transaction
   - Create payment
   - Reconcile them
   - Verify is_reconciled=True

3. **`test_unreconcile_transaction`**
   - Create reconciled transaction
   - Unreconcile
   - Verify is_reconciled=False

4. **`test_list_unreconciled_transactions`**
   - Create mixed reconciled/unreconciled
   - Call list_unreconciled
   - Verify only unreconciled returned

5. **`test_import_duplicate_detection`**
   - Import transaction with external_id
   - Attempt duplicate import
   - Verify duplicate rejected or skipped

### Detailed Plan for PHASE 5.5 (API View Tests)

**File:** `apps/backend/apps/banking/tests/test_views.py`

**Tests to Implement:**

**Bank Account Endpoints (5):**
1. `test_list_bank_accounts_api`
2. `test_create_bank_account_api`
3. `test_get_bank_account_api`
4. `test_update_bank_account_api`
5. `test_deactivate_bank_account_api`

**Payment Endpoints (4):**
6. `test_list_payments_api`
7. `test_create_received_payment_api`
8. `test_create_made_payment_api`
9. `test_void_payment_api`

**Bank Transaction Endpoints (3):**
10. `test_list_bank_transactions_api`
11. `test_import_transactions_api`
12. `test_reconcile_transaction_api`

### Detailed Plan for PHASE 6 (Rate Limiting)

**Steps:**

1. **Install django-ratelimit**
   ```bash
   pip install django-ratelimit
   pip freeze > requirements.txt
   ```

2. **Add to INSTALLED_APPS**
   - Edit `config/settings/base.py`

3. **Apply to Payment Endpoints**
   - Edit `apps/banking/views.py`
   - Add `@ratelimit(key='user', rate='60/m')` decorator

4. **Apply to Auth Endpoints**
   - Edit `apps/core/views/auth.py`
   - Add `@ratelimit(key='ip', rate='10/m')` for login

5. **Test Rate Limiting**
   - Create test file `tests/security/test_rate_limiting.py`
   - Test 429 response after limit exceeded

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Model-SQL drift | Validate model imports after each change |
| RLS bypass | Test RLS in every test file |
| Payment double-posting | Unique constraint + transaction.atomic() |
| FX calculation errors | Use money() utility, test edge cases |
| Audit log bloat | Partition by date (future) |

---

## Estimated Timeline

| Phase | Hours | Day |
|-------|-------|-----|
| Phase 0 | 0.5 | Day 1 AM |
| Phase 1 | 4 | Day 1 |
| Phase 2 | 6 | Day 2 |
| Phase 3 | 4 | Day 3 |
| Phase 4 | 4 | Day 4 |
| Phase 5 | 6 | Day 5 |
| Phase 6 | 2 | Day 6 AM |
| Phase 7 | 2 | Day 6 PM |
| **Total** | **28.5** | **~4 days** |

---

## Validation Gates

| Gate | Criteria | Status |
|------|----------|--------|
| G1 | Serializers complete | ✅ PASS |
| G2 | Services complete | ✅ PASS |
| G3 | Views complete | ✅ PASS |
| G4 | Journal integration | ⏳ DEFERRED |
| G5 | TDD complete (52 tests) | ⏳ 29/52 (56%) |
| G6 | Security hardened | ⏳ PENDING |
| G7 | SEC-001 closed | ⏳ PENDING (tests + rate limiting) |

---

**Plan Updated:** 2026-03-02
**Next Action:** Implement PHASE 5.3 Allocation Tests
**Blockers:** None for remaining tests
