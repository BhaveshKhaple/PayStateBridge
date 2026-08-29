# Slice 4 — Razorpay Test Mode

**Phase goal:** Startup guards, recovery permit, FakePaymentProvider for CI, Razorpay Test Mode adapter, HMAC webhook verification.
**Date target:** 03/09/2026
**Tasks:** S4-01, S4-02, S4-03
**Cut line:** Test Mode keys only. FakePaymentProvider in all CI tests. Live key config rejected at startup.

## Acceptance criteria

- [ ] App refuses startup if RAZORPAY_KEY_ID doesn't start with `rzp_test_` (when set)
- [ ] APP_ENV != "demo" rejects startup
- [ ] PENDING/UNKNOWN/CAPTURED cases cannot obtain a RecoveryPermit
- [ ] FAILED case → one permit with expiry + stable idempotency key
- [ ] Repeated permit request returns existing record, not new one
- [ ] FakePaymentProvider runs in CI without credentials
- [ ] Razorpay adapter creates one Test Mode link from valid permit
- [ ] Second click returns same stored link ID (idempotent)
- [ ] Invalid HMAC webhook → 400, no state change
- [ ] Duplicate event ID → idempotent, no double transition
- [ ] Valid Test Mode paid event → case moves to RECOVERY_PAID_TEST
- [ ] UI: FAILED case shows "Create Test Mode recovery link" button; PENDING shows disabled
