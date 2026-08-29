# Product Requirements — PayState Bridge

**Research date:** 30/08/2026  
**Track:** Razorpay AI Buildathon, Track 03 — AI Revenue Recovery  
**Maturity:** portfolio-grade proof of concept. Synthetic incidents and Razorpay Test Mode only.

## 1. One-sentence mission

**For a merchant-support operator facing a customer whose payment appears debited but unresolved, PayState Bridge determines the safest next action before asking the customer to pay again—so the merchant avoids duplicate payments, recovers captured-but-unlinked orders, and creates an evidence-backed recovery case.**

## 2. Why this problem exists

A UPI payment crosses several systems: customer app, remitter bank, NPCI rail, beneficiary/acquiring bank, gateway, and merchant order system. A customer may see money debited while the merchant has no confirmed order yet. The harmful operational default is often: **“please pay again.”**

That creates a second payment while the first one is still `PENDING` or has already succeeded without creating an order. The result is a duplicate payment, refund chase, support cost, and loss of customer trust.

This is not a claim that PayState Bridge can control NPCI, PhonePe, Google Pay, or bank settlement. It cannot. The v0 product solves the merchant-controlled decision:

> **Should the merchant wait, reconcile an existing payment, issue one replacement link, create a duplicate refund-review case, or give the customer an evidence packet for the official escalation route?**

## 3. Track fit

Track 03 asks for: **payment degradation → root cause → bounded recovery action**, measured money recovered across a batch, stopping rules, compliant escalation, and an audit trail.

| Track requirement | PayState Bridge behavior |
|---|---|
| Detect revenue at risk | Identifies orders where payment/order records disagree or customer says debit occurred but order is unresolved. |
| Diagnose root cause | Classifies payment cases into safe, explainable categories. |
| Execute bounded recovery | Links captured payment to an order, creates one replacement Test Mode link only after verified failure, or prepares human-reviewed refund case. |
| Show money recovered | Reports simulated GMV recovered from captured-but-unlinked orders and verified replacement payments. |
| Stopping rules | Blocks a new link while original payment is `PENDING` or `OUTCOME_UNKNOWN`. |
| Audit trail | Every status source, evidence record, policy decision, action, and operator approval is logged. |

## 4. Primary user and core job

### Primary user

A small merchant’s support or operations person handling a customer message such as:

> “My account was debited through PhonePe, but I did not get an order confirmation. Should I pay again?”

### Core job

Determine the next safe merchant action in under one minute without guessing about the first payment.

### Smallest meaningful vertical slice

A support operator opens one synthetic incident. The first payment is `PENDING` in the merchant/gateway event stream. PayState Bridge says **DO NOT RETRY**, sends a safe customer message, stores the audit event, and gives a next-check time. Later a simulated event changes the payment to `CAPTURED`; the system links it to the order instead of issuing a second payment link.

**Success signal:** In the initial test suite, no replacement link is created for a `PENDING` or `OUTCOME_UNKNOWN` original payment.

## 5. Supported case taxonomy

| Case | Plain-language meaning | v0 merchant action |
|---|---|---|
| `PENDING` | Money may be debited, but the final payment result is not known yet. | Do not retry; wait/reconcile; show customer status. |
| `FAILED` | Merchant/gateway evidence conclusively says the original payment failed. | Create exactly one replacement Test Mode link. |
| `CAPTURED_UNLINKED` | Payment succeeded, but the merchant order was not created/linked. | Attach existing payment to order; recover the sale without charging again. |
| `DUPLICATE_SUCCESS` | Two successful payment records map to one intended order. | Create refund-review case; no automatic refund. |
| `OUTCOME_UNKNOWN` | Evidence conflicts or key data is missing. | Do not retry; create evidence packet and human-review/escalation path. |
| `WRONG_RECIPIENT` | Customer successfully sent money to wrong UPI ID/person. | Explain limitation; provide official bank/NPCI evidence packet. No recovery claim. |
| `UNAUTHORIZED` | Customer says they did not initiate payment. | Stop merchant recovery flow; route to bank/cybercrime/human escalation guidance. |

## 6. In scope for v0

- Synthetic merchant orders, payment events, bank/app screenshots, UTR-like references, customer messages, and support cases.
- Deterministic classification using merchant-side payment events plus submitted evidence.
- Gemini structured extraction for optional customer text/synthetic screenshot extraction; deterministic logic makes the final decision.
- Buyer-facing "do not pay again" or recovery-status message.
- Razorpay Test Mode Payment Link creation only after `FAILED` state and a server-generated recovery permit.
- Webhook/callback verification and idempotent event receipts.
- Held-out synthetic evaluation set and report.

## 7. Explicitly deferred

- Direct PhonePe, Google Pay, NPCI, UPI switch, or bank-core integration.
- Live payment data, customer bank statements, real PII, real customer screenshots, real money, live refunds, direct complaint submission, or legal-advice workflow.
- Guaranteed recovery, forced reversal of wrong-recipient transfer, fraud investigation, or cybercrime reporting automation.
- Multi-merchant tenancy, full WhatsApp integration, autonomous outbound calls, model fine-tuning, vector database, blockchain, multi-agent systems, and Kubernetes.

## 8. Product requirements

| ID | Requirement | Acceptance criterion |
|---|---|---|
| PR-01 | Operator can create a case from synthetic order/payment evidence and optional customer message. | Case is stored with redacted identifiers and one of the defined states. |
| PR-02 | System separates app-reported customer information from authoritative merchant/gateway event evidence. | UI labels evidence source and confidence; customer text alone never changes payment state. |
| PR-03 | Recovery policy is deterministic. | Same input events and policy version always yield same action. |
| PR-04 | No replacement link exists unless original state is `FAILED`. | Safety tests show zero links for `PENDING` / `OUTCOME_UNKNOWN`. |
| PR-05 | Captured-but-unlinked payment can be attached to an order. | Order becomes `PAID_RECONCILED` without a new charge. |
| PR-06 | Duplicate success creates a review case, not automatic refund. | Human approval requirement visible before any refund action. |
| PR-07 | Every decision has an audit record. | Audit contains source IDs, previous/new state, rule, actor, timestamp, and action. |
| PR-08 | Razorpay callback/webhook is verified server-side. | Invalid HMAC/body does not alter a case. |
| PR-09 | Customer communication is bounded. | Agent never promises bank reversal, exact refund timing, or recovery outside verified rules. |

## 9. User-visible flows

### Flow A — Pending payment: stop harmful retry

1. Customer says money was debited but order is absent.
2. Operator finds order and payment reference.
3. Gateway event is `PENDING`; no final receipt exists.
4. PayState Bridge labels state `PENDING` and blocks `CREATE_REPLACEMENT_LINK`.
5. Customer sees: “We are verifying your payment. Please do not pay again. We will confirm the order if the payment completes, or guide you after the payment is conclusively marked failed.”
6. Audit records action and recheck deadline.

### Flow B — Captured payment but no order: recover revenue

1. Gateway event says payment captured.
2. Merchant order is still `PAYMENT_PENDING` because webhook/order-link flow failed.
3. System verifies amount/reference/order match.
4. It creates/updates the order to `PAID_RECONCILED`.
5. Merchant recovers the sale without customer paying again.

### Flow C — Verified failure: safe recovery

1. Original payment has a final `FAILED` event.
2. System creates one short-lived Test Mode recovery link tied to the original order and recovery case.
3. Repeated button click returns same link/action because idempotency key is reused.

### Flow D — Duplicate success: protect customer and merchant

1. Two captured payments map to same intended order.
2. System opens `DUPLICATE_REVIEW` with both references and amount comparison.
3. Operator approves a simulated refund-review action; v0 does not execute live refund.

## 10. Measurable outcome

| Metric | v0 definition |
|---|---|
| Unsafe retry-link rate | Replacement links created when original payment was `PENDING` or `OUTCOME_UNKNOWN`; target 0. |
| State classification accuracy | Correct final state over held-out synthetic incidents. |
| Captured-unlinked recovery rate | Correctly linked captured payments divided by all such cases. |
| Duplicate-success detection recall | Detected duplicate-success cases divided by known duplicate-success cases. |
| Simulated GMV recovered | Sum of orders reconciled from captured payments plus successfully completed verified recovery links. |
| Evidence-packet completeness | Cases with required order/payment/UTR-like/time fields and official route. |

## 11. Known risks and honest claims

- Test Mode cannot reproduce bank settlement timing or real UPI reconciliation.
- A synthetic screenshot/UTR is not authoritative proof of bank debit.
- App-specific support windows differ; official policy pages can change.
- The prototype is a merchant decision-support system, not a consumer grievance authority.
- All recovery metrics are simulated and must be labelled as such in the README, UI, video, and pitch.
