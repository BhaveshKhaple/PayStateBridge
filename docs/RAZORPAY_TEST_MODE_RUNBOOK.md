# Razorpay Test Mode Runbook — PayState Bridge

> This runbook is for a Buildathon prototype. It permits simulated Test Mode Payment Links only. It does not authorize Live Mode, real-money payments, direct UPI rail access, bank access, or live refunds.

## 1. What Razorpay Test Mode proves

It proves the merchant-side decision boundary:

```text
verified original FAILURE
→ one recovery permit
→ one Test Mode link
→ verified callback/webhook
→ recovered order state
```

It does **not** prove bank settlement, PhonePe/GPay state, NPCI reversal, or actual customer money recovery.

## 2. Official facts checked 30/08/2026

- Razorpay Payment Links can be created/fetched/cancelled and have callback parameters that must be signature-verified server-side.
- Razorpay documents webhook events such as `payment_link.paid`, `payment_link.partially_paid`, `payment_link.cancelled`, and `payment_link.expired`.
- Current Test Mode documentation states a limit of **30 Payment Links per business**.
- Webhook signature verification must use the raw request body; duplicate/out-of-order handling is needed.

Sources:

- [Payment Links APIs](https://razorpay.com/docs/payments/payment-links/apis/)
- [Create/Test Payment Links](https://razorpay.com/docs/payments/payment-links/create/)
- [Payment Link webhooks](https://razorpay.com/docs/webhooks/payment-links/)
- [Webhook validation](https://razorpay.com/docs/webhooks/validate-test/)

Re-check before implementation.

## 3. Environment variables

```bash
# apps/api/.env.local — never commit
APP_ENV=demo
PAYMENT_PROVIDER=razorpay_test
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=unique-secret-for-this-demo
PUBLIC_APP_URL=https://your-staging-url.example
```

### Startup guard

Fail startup if any condition is false:

```text
APP_ENV == demo
PAYMENT_PROVIDER == razorpay_test
RAZORPAY_KEY_ID starts with rzp_test_
```

No secret may appear in `.env.example`, repository, video, screenshot, frontend bundle, audit event, error message, GitHub Actions cache, or PR output.

## 4. Recovery-link preconditions

The API route must reject a request unless all are true:

```text
case.state == FAILED
AND case.action == CREATE_RECOVERY_PERMIT
AND verified gateway event has final failed status
AND merchant order remains unpaid
AND no captured payment matches the order
AND no active recovery action exists for same case
AND recovery permit is unexpired
AND environment is Test Mode
```

This is the product’s main safety guarantee.

## 5. Recovery-link creation flow

1. Operator resolves case through deterministic engine.
2. Server creates short-lived `RecoveryPermit` with case/order/original payment/amount/idempotency key.
3. Server calls Razorpay create Payment Link API with:
   - amount in paise;
   - internal reference ID such as `PSB-{case_id}-{hash}`;
   - short expiry;
   - callback URL;
   - no real customer contact/address in demo.
4. Server stores returned payment-link ID and link URL against the recovery action.
5. UI shows **Test Mode recovery link**, original failed payment reference, and expiry.
6. Repeated request with same case returns stored action; it never creates another link.

## 6. Callback and webhook verification

### Callback

A callback URL is convenient but not authoritative by itself.

1. Receive `razorpay_payment_link_id`, reference, status, payment ID, and signature.
2. Find stored recovery action by link/reference.
3. Construct documented signature payload.
4. Verify with key secret server-side.
5. Store `CALLBACK_VERIFIED`; do not rely on browser query parameters as truth.

### Webhook

`POST /v1/webhooks/razorpay`

1. Read **raw bytes** before parsing JSON.
2. Read `X-Razorpay-Signature` and `x-razorpay-event-id` headers.
3. HMAC-SHA256 raw body using webhook secret; constant-time compare.
4. Invalid signature → no parse/state update; record redacted security event.
5. Duplicate event ID → return success/no-op; one receipt only.
6. Parse valid payload and apply only legal state transition.
7. Do not assume events arrive in order.

## 7. Manual Test Mode matrix

| Scenario | Expected behavior |
|---|---|
| Original `PENDING` case | Recovery button unavailable; no Razorpay API call. |
| Original `FAILED` case | Exactly one Test Mode recovery link created. |
| Same failed case clicked twice | Same stored recovery action/link returned. |
| Test payment succeeds | Valid callback/webhook moves case to `RECOVERY_PAID_TEST`; order marked recovered. |
| Test payment fails | Case remains recoverable/pending policy state; no false paid order. |
| Altered callback/webhook body | Signature fails; no state change. |
| Same webhook sent twice | One state transition. |
| Link expires | Recovery action reflects expiration; human/operator can decide next state. |

## 8. Public endpoint caveat

Webhook delivery needs a publicly reachable staging endpoint. Razorpay docs say localhost cannot receive webhook delivery directly. Use a permitted staging URL or supported tunnel only when the deterministic core already works.

If no public endpoint is available by 03/09:

- retain fully tested `FakePaymentProvider`;
- show policy and event-receipt tests;
- disclose that real Test Mode webhook delivery was not demonstrated;
- do not fake success.

## 9. Never do these actions

- Never use Live Mode key.
- Never request user UPI PIN, OTP, account statement, card number, CVV, or real UPI ID.
- Never issue a new link for `PENDING` / `OUTCOME_UNKNOWN`.
- Never automatically refund duplicate payment in v0.
- Never say payment was recovered unless verified provider/Test Mode evidence exists.
