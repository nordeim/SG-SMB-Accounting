# Banking Module Execution Plan
## SEC-001 (HIGH) Remediation

**Version:** 1.0.0  
**Date:** 2026-03-01  
**Status:** VALIDATED - Ready for Implementation

---

## Executive Summary

This execution plan remediates **SEC-001 (HIGH Severity)** by replacing stub implementations in `apps/backend/apps/banking/views.py` with production-grade, validated endpoints.

**Key Corrections from Draft Plan:**
- Models are located in `apps/core/models/`, NOT `apps/banking/models/`
- `BankTransaction` model is MISSING - must be created
- Serializers and Services will be created in `apps/banking/`

---

## Phase 0: Pre-Implementation Setup (30 min)

### 0.1 Create BankTransaction Model
**File:** `apps/backend/apps/core/models/bank_transaction.py`

```python
# Maps to banking.bank_transaction table (SQL lines 1315-1348)
```

**Checklist:**
- [ ] Create `bank_transaction.py` model file
- [ ] Add to `apps/core/models/__init__.py` exports
- [ ] Verify model imports without errors
- [ ] Confirm SQL alignment (14 columns)

### 0.2 Create Directory Structure
```bash
mkdir -p apps/backend/apps/banking/serializers
mkdir -p apps/backend/apps/banking/services
mkdir -p apps/backend/apps/banking/tests
touch apps/backend/apps/banking/serializers/__init__.py
touch apps/backend/apps/banking/services/__init__.py
touch apps/backend/apps/banking/tests/__init__.py
```

---

## Phase 1: Serializers & Validation (4 hours)

### 1.1 BankAccountSerializer
**File:** `apps/backend/apps/banking/serializers/bank_account.py`

| Field | Validation | SQL Constraint |
|-------|-----------|----------------|
| account_name | max_length=150, required | NOT NULL |
| account_number | max_length=30, required, unique per org | UNIQUE(org_id, account_number) |
| bank_name | max_length=100, required | NOT NULL |
| bank_code | max_length=20, optional | - |
| branch_code | max_length=20, optional | - |
| currency | max_length=3, default='SGD' | DEFAULT 'SGD' |
| gl_account | FK validation, required | NOT NULL |
| paynow_type | ChoiceField: UEN/MOBILE/NRIC | CHECK constraint |
| paynow_id | Conditional: required if paynow_type set | - |
| opening_balance | DecimalField(10,4), min=0 | NUMERIC(10,4) |
| opening_balance_date | DateField, optional | - |

**Custom Validators:**
- [ ] `validate_paynow()` - If paynow_type set, paynow_id required
- [ ] `validate_gl_account()` - Must belong to org and be bank account type

### 1.2 PaymentSerializer
**File:** `apps/backend/apps/banking/serializers/payment.py`

| Field | Validation | SQL Constraint |
|-------|-----------|----------------|
| payment_type | ChoiceField: RECEIVED/MADE | CHECK constraint |
| payment_date | DateField, required | NOT NULL |
| contact | FK validation, required | NOT NULL |
| bank_account | FK validation, org ownership | NOT NULL |
| amount | DecimalField(10,4), min=0.0001 | CHECK (amount > 0) |
| currency | max_length=3, default='SGD' | DEFAULT 'SGD' |
| exchange_rate | DecimalField(12,6), min=0.000001 | DEFAULT 1.000000 |
| payment_method | ChoiceField: 7 options | CHECK constraint |
| payment_reference | max_length=100, optional | - |

**Custom Validators:**
- [ ] `validate_contact_type()` - RECEIVED requires customer, MADE requires supplier
- [ ] `validate_bank_account_org()` - Must belong to current org

### 1.3 PaymentAllocationSerializer
**File:** `apps/backend/apps/banking/serializers/allocation.py`

| Field | Validation | SQL Constraint |
|-------|-----------|----------------|
| payment | FK validation, required | NOT NULL |
| document | FK validation, required | NOT NULL |
| allocated_amount | DecimalField(10,4), min=0.0001 | CHECK (allocated_amount > 0) |

**Custom Validators:**
- [ ] `validate_document_status()` - Document must be APPROVED
- [ ] `validate_allocation_not_exceed()` - Total allocations ≤ payment amount
- [ ] `validate_unique_allocation()` - UNIQUE(payment_id, document_id)

### 1.4 BankTransactionSerializer
**File:** `apps/backend/apps/banking/serializers/bank_transaction.py`

| Field | Validation | SQL Constraint |
|-------|-----------|----------------|
| bank_account | FK validation, required | NOT NULL |
| transaction_date | DateField, required | NOT NULL |
| value_date | DateField, optional | - |
| description | TextField, required | NOT NULL |
| reference | max_length=100, optional | - |
| amount | DecimalField(10,4), can be negative | NOT NULL |
| running_balance | DecimalField(10,4), optional | - |
| import_source | ChoiceField: CSV/OFX/MT940/API | - |

**Checklist:**
- [ ] All 4 serializers created
- [ ] Unit tests for each validator (12 tests minimum)
- [ ] Decimal precision validated (use money() utility)
- [ ] All tests pass

---

## Phase 2: Service Layer (6 hours)

### 2.1 BankAccountService
**File:** `apps/backend/apps/banking/services/bank_account_service.py`

**Methods:**
| Method | Description | Transaction |
|--------|-------------|-------------|
| `create(org_id, data, user)` | Create bank account with GL linkage | `@transaction.atomic()` |
| `update(org_id, account_id, data)` | Update bank account details | `@transaction.atomic()` |
| `deactivate(org_id, account_id)` | Soft delete (set is_active=False) | `@transaction.atomic()` |
| `list(org_id, filters)` | List accounts with pagination | Read-only |
| `get(org_id, account_id)` | Get single account | Read-only |

**Business Logic:**
- [ ] Validate GL account is bank-type asset account
- [ ] Only one default bank account per org
- [ ] Opening balance creates initial journal entry
- [ ] Audit log on all mutations

### 2.2 PaymentService
**File:** `apps/backend/apps/banking/services/payment_service.py`

**Methods:**
| Method | Description | Journal Entry |
|--------|-------------|---------------|
| `create_received(org_id, data, user)` | Customer payment | Debit Bank, Credit AR |
| `create_made(org_id, data, user)` | Supplier payment | Debit AP, Credit Bank |
| `allocate(payment, allocations)` | Allocate to invoices | - |
| `void(org_id, payment_id, user)` | Void payment | Reversal entry |
| `list(org_id, filters)` | List payments | Read-only |

**Business Logic:**
- [ ] Generate payment number via `core.get_next_document_number()`
- [ ] Calculate base_amount for multi-currency
- [ ] FX gain/loss calculation on allocation
- [ ] Journal entry auto-creation
- [ ] Audit log on all mutations

### 2.3 PaymentAllocationService
**File:** `apps/backend/apps/banking/services/allocation_service.py`

**Methods:**
| Method | Description |
|--------|-------------|
| `allocate(payment, allocations, user)` | Allocate payment to documents |
| `unallocate(allocation_id, user)` | Remove allocation |
| `get_payment_allocations(payment_id)` | List allocations for payment |

**Business Logic:**
- [ ] Validate total ≤ payment amount
- [ ] Calculate FX gain/loss for multi-currency
- [ ] Update document status (PARTIALLY_PAID, PAID)
- [ ] Audit log

### 2.4 BankTransactionService
**File:** `apps/backend/apps/banking/services/reconciliation_service.py`

**Methods:**
| Method | Description |
|--------|-------------|
| `import_csv(org_id, bank_account_id, file)` | Import bank statement CSV |
| `reconcile(transaction_id, payment_id)` | Match transaction to payment |
| `unreconcile(transaction_id)` | Remove reconciliation |
| `list_unreconciled(org_id, bank_account_id)` | List unmatched transactions |

**Checklist:**
- [ ] All 4 services created
- [ ] All methods use `@transaction.atomic()` for writes
- [ ] All monetary values use `money()` utility
- [ ] All mutations trigger audit logging
- [ ] Integration tests pass (15 tests minimum)

---

## Phase 3: API Views (4 hours)

### 3.1 BankAccount Views
**File:** `apps/backend/apps/banking/views.py` (Replace stubs)

| Endpoint | Method | Permission | Service |
|----------|--------|------------|---------|
| `/bank-accounts/` | GET | IsOrgMember | BankAccountService.list() |
| `/bank-accounts/` | POST | CanManageBanking | BankAccountService.create() |
| `/bank-accounts/{id}/` | GET | IsOrgMember | BankAccountService.get() |
| `/bank-accounts/{id}/` | PUT | CanManageBanking | BankAccountService.update() |
| `/bank-accounts/{id}/` | DELETE | CanManageBanking | BankAccountService.deactivate() |

### 3.2 Payment Views

| Endpoint | Method | Permission | Service |
|----------|--------|------------|---------|
| `/payments/` | GET | IsOrgMember | PaymentService.list() |
| `/payments/receive/` | POST | CanManageBanking | PaymentService.create_received() |
| `/payments/make/` | POST | CanManageBanking | PaymentService.create_made() |
| `/payments/{id}/allocate/` | POST | CanManageBanking | PaymentAllocationService.allocate() |
| `/payments/{id}/void/` | POST | CanManageBanking | PaymentService.void() |

### 3.3 Bank Transaction Views

| Endpoint | Method | Permission | Service |
|----------|--------|------------|---------|
| `/bank-transactions/` | GET | IsOrgMember | BankTransactionService.list() |
| `/bank-transactions/import/` | POST | CanManageBanking | BankTransactionService.import_csv() |
| `/bank-transactions/{id}/reconcile/` | POST | CanManageBanking | BankTransactionService.reconcile() |

**Checklist:**
- [ ] All 12 endpoints implemented
- [ ] All use proper serializer validation
- [ ] All have correct permission classes
- [ ] All wrap responses with `@wrap_response`
- [ ] API tests pass (12 tests minimum)

---

## Phase 4: Journal Integration (4 hours)

### 4.1 Payment Journal Entries

**Customer Payment (RECEIVED):**
```
Debit:  Bank Account (gl_account)    = amount
Credit: Accounts Receivable          = amount
```

**Supplier Payment (MADE):**
```
Debit:  Accounts Payable             = amount
Credit: Bank Account (gl_account)    = amount
```

**Multi-Currency FX Gain/Loss:**
```
If base_amount differs from allocated base:
  FX Gain: Credit FX Gain account
  FX Loss: Debit FX Loss account
```

### 4.2 Journal Service Integration

**Checklist:**
- [ ] Journal entry created on payment creation
- [ ] FX gain/loss calculated on allocation
- [ ] Reversal entry created on void
- [ ] Double-entry balance validated
- [ ] Integration tests pass (5 tests minimum)

---

## Phase 5: TDD Testing (6 hours)

### 5.1 Test Structure
```
apps/backend/apps/banking/tests/
├── __init__.py
├── test_bank_account_service.py   # 12 tests
├── test_payment_service.py        # 15 tests
├── test_allocation_service.py     # 8 tests
├── test_reconciliation_service.py # 5 tests
└── test_views.py                  # 12 tests
```

### 5.2 Test Categories

**Bank Account Tests (12):**
1. `test_create_bank_account_success`
2. `test_create_bank_account_duplicate_number`
3. `test_create_bank_account_invalid_gl_account`
4. `test_create_bank_account_paynow_validation`
5. `test_update_bank_account_success`
6. `test_update_bank_account_wrong_org`
7. `test_deactivate_bank_account_success`
8. `test_deactivate_bank_account_with_balance`
9. `test_list_bank_accounts_pagination`
10. `test_get_bank_account_not_found`
11. `test_bank_account_rls_enforcement`
12. `test_bank_account_audit_logged`

**Payment Tests (15):**
1. `test_create_received_payment_success`
2. `test_create_made_payment_success`
3. `test_create_payment_invalid_amount`
4. `test_create_payment_contact_not_customer`
5. `test_create_payment_bank_account_wrong_org`
6. `test_create_payment_with_allocations`
7. `test_create_payment_journal_entry_created`
8. `test_create_payment_audit_logged`
9. `test_void_payment_reverses_journal`
10. `test_multi_currency_payment_fx_calculated`
11. `test_payment_number_unique_per_org`
12. `test_payment_number_sequencing`
13. `test_payment_rls_enforcement`
14. `test_payment_list_filtering`
15. `test_payment_pagination`

**Allocation Tests (8):**
1. `test_allocate_payment_to_invoice`
2. `test_allocate_partial_payment`
3. `test_allocate_exceeds_payment_amount`
4. `test_allocate_to_non_approved_invoice`
5. `test_allocate_duplicate_invoice`
6. `test_unallocate_payment`
7. `test_allocation_updates_invoice_status`
8. `test_allocation_fx_gain_loss`

**Reconciliation Tests (5):**
1. `test_import_csv_success`
2. `test_reconcile_transaction_to_payment`
3. `test_unreconcile_transaction`
4. `test_list_unreconciled_transactions`
5. `test_import_duplicate_detection`

**API View Tests (12):**
- All endpoint tests from Section 3

**Total Target: 52 tests**

---

## Phase 6: Security Hardening (2 hours)

### 6.1 Input Validation
- [ ] All inputs sanitized via serializers
- [ ] No raw `request.data.get()` usage
- [ ] Decimal fields reject floats

### 6.2 Authorization
- [ ] All write operations require `CanManageBanking`
- [ ] All read operations require `IsOrgMember`
- [ ] RLS policies verified in tests

### 6.3 Audit Logging
- [ ] All mutations logged to `audit.event_log`
- [ ] Before/after values captured
- [ ] User attribution correct

### 6.4 Rate Limiting (SEC-002)
- [ ] Install `django-ratelimit`
- [ ] Apply to payment endpoints (60/min)

---

## Phase 7: Documentation (2 hours)

### 7.1 Files to Update
- [ ] `README.md` - Mark SEC-001 as remediated
- [ ] `AGENTS.md` - Update security status
- [ ] `API_CLI_Usage_Guide.md` - Add banking examples
- [ ] `ACCOMPLISHMENTS.md` - Record implementation

### 7.2 SEC-001 Closure Checklist
- [ ] All stub code replaced
- [ ] All tests passing (52+)
- [ ] Security audit re-scan
- [ ] Documentation updated
- [ ] PR created and reviewed

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

| Gate | Criteria | Pass Condition |
|------|----------|----------------|
| G1 | Serializers complete | Unit tests pass |
| G2 | Services complete | Integration tests pass |
| G3 | Views complete | API tests pass |
| G4 | Journal integration | Double-entry verified |
| G5 | TDD complete | 52+ tests pass |
| G6 | Security hardened | Security scan clean |
| G7 | SEC-001 closed | Audit confirmed |

---

**Plan Validated:** ✅  
**Ready for Implementation:** ✅  
**Blockers:** None
