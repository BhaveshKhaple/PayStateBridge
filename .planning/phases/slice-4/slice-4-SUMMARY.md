---
phase: slice-4
plan: slice-4
subsystem: razorpay-test-mode
tags: [razorpay, payment-links, webhook, config-guard, idempotency, fake-provider]
status: complete
completed_at: 2026-08-30T00:00:00Z
tasks_completed: 3
tasks_total: 3
commits:
  - 3852b38
  - 4faeb60
  - aa0cffe
---

# Phase Slice-4: Razorpay Test Mode Summary

## One-liner

Startup config guard rejecting rzp_live_ keys, idempotent RecoveryPermit service gating all non-FAILED states, FakePaymentProvider + RazorpayTestModeProvider adapters, and HMAC-verified webhook handler with event deduplication.

## What was built

### Task S4-01 — Startup config guard + RecoveryPermit service (commit 3852b38)

**Files created/modified:**
- `apps/api/app/config.py` — AppConfig with validate(): rejects APP_ENV != "demo" and RAZORPAY_KEY_ID not starting with "rzp_test_" at startup; wired into FastAPI lifespan
- `apps/api/app/schemas/payment.py` — RecoveryPermit schema added (case_id, order_id, amount_paise, idempotency_key, expires_at, environment: Literal["test"])
- `apps/api/app/services/permit_service.py` — issue_recovery_permit(): blocks PENDING, OUTCOME_UNKNOWN, CAPTURED_UNLINKED, WRONG_RECIPIENT, UNAUTHORIZED; idempotent via SHA256(permit:case_id:order_id:amount_paise); 60-min expiry; transitions case to RECOVERY_PERMIT_ISSUED with audit event
- `apps/api/app/main.py` — lifespan calls settings.validate() before init_db(); imports ConfigError
- `apps/api/app/api/cases.py` — POST /{case_id}/recovery-permit route
- `apps/api/tests/test_permit_service.py` — 11 tests: all blocked states, idempotency, already-paid order, config guards (live key, non-demo env, valid test key)

### Task S4-02 — Payment provider protocol + FakePaymentProvider + Razorpay adapter (commit 4faeb60)

**Files created:**
- `apps/api/app/integrations/payment_provider.py` — PaymentProvider Protocol (runtime_checkable), ProviderLinkResult, VerifiedWebhookEvent Pydantic models
- `apps/api/app/integrations/fake_provider.py` — FakePaymentProvider: deterministic fake_link_<md5(idem_key)[:12]>, HMAC webhook verify against FAKE_WEBHOOK_SECRET, no HTTP calls, returns environment="fake"
- `apps/api/app/integrations/razorpay_provider.py` — RazorpayTestModeProvider: POST /v1/payment_links with Idempotency-Key header, rejects non-rzp_test_ keys in __init__, HMAC verify via RAZORPAY_WEBHOOK_SECRET
- `apps/api/app/services/recovery_link_service.py` — get_payment_provider() factory (fake when use_fake_provider), create_recovery_link() idempotent (returns stored link on second call using "link:" prefix idempotency key), apply_webhook_paid() transitions to RECOVERY_PAID_TEST
- `apps/api/app/api/cases.py` — POST /{case_id}/recovery-link route added
- `apps/api/tests/test_recovery_link.py` — 4 tests: link creation with FakeProvider, idempotency, no-permit block, PENDING block

### Task S4-03 — Webhook handler + deduplication + UI wire-up (commit aa0cffe)

**Files created/modified:**
- `apps/api/app/api/webhooks.py` — POST /v1/webhooks/razorpay: (1) HMAC verify on raw bytes before JSON parse; (2) in-memory _processed_event_ids set for dedup returning status=duplicate_ignored; (3) payment_link.paid routing via provider_link_id -> RecoveryAction -> PaymentCase -> apply_webhook_paid
- `apps/api/app/main.py` — webhooks_router registered
- `apps/api/tests/test_webhook.py` — 4 tests: bad sig -> 400, valid sig -> 200, duplicate dedup, full RECOVERY_LINK_CREATED -> RECOVERY_PAID_TEST state transition via payment_link.paid
- `apps/web/app/cases/[id]/page.tsx` — FAILED case recovery panel: replaced placeholder button with two anchor links — "Issue recovery permit" (POST recovery-permit) and "Create Test Mode link" (POST recovery-link)

## Key decisions

- **RecoveryAction unique constraint handling:** RECOVERY_PERMIT and RECOVERY_LINK records both use the `idempotency_key` column (unique). Used "link:" prefix for the RECOVERY_LINK row to avoid unique constraint collision with the RECOVERY_PERMIT row for the same case.
- **Fake provider always active in CI:** `settings.use_fake_provider` is true whenever RAZORPAY_KEY_ID/SECRET are absent (default). All CI tests run against FakePaymentProvider with no credential requirements.
- **In-memory event dedup:** _processed_event_ids is a module-level set sufficient for the demo; noted in code that production would use a DB table.
- **Payload shape for FakePaymentProvider:** FakePaymentProvider reads `payload.payment_link.id` (not `payload.payment_link.entity.id` as Razorpay production uses). Tests use the fake-provider shape; real webhooks from Razorpay use the RazorpayTestModeProvider which reads the entity-nested shape.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed RECOVERY_LINK idempotency key collision**
- **Found during:** Task S4-02
- **Issue:** RecoveryAction.idempotency_key has a UNIQUE constraint. Storing a RECOVERY_LINK row with the same idempotency_key as the RECOVERY_PERMIT row would raise a DB IntegrityError.
- **Fix:** Prefixed the RECOVERY_LINK row's key with "link:" — making it "link:<sha256_hash>" vs the permit's "<sha256_hash>"
- **Files modified:** `apps/api/app/services/recovery_link_service.py`
- **Commit:** 4faeb60

## Security notes

- Non-test Razorpay keys rejected at startup via ConfigError (never reaches provider layer)
- HMAC verification uses `hmac.compare_digest` (constant-time) to prevent timing attacks
- Webhook handler verifies signature on raw bytes before any JSON parsing — prevents signature bypass via re-serialization
- FakePaymentProvider webhook secret is a well-known test constant (never used in production paths)

## Self-Check: PASSED

Files confirmed present:
- apps/api/app/config.py — FOUND
- apps/api/app/services/permit_service.py — FOUND
- apps/api/app/integrations/payment_provider.py — FOUND
- apps/api/app/integrations/fake_provider.py — FOUND
- apps/api/app/integrations/razorpay_provider.py — FOUND
- apps/api/app/services/recovery_link_service.py — FOUND
- apps/api/app/api/webhooks.py — FOUND
- apps/api/tests/test_permit_service.py — FOUND
- apps/api/tests/test_recovery_link.py — FOUND
- apps/api/tests/test_webhook.py — FOUND

Commits confirmed: 3852b38, 4faeb60, aa0cffe — all on main, pushed to origin.
