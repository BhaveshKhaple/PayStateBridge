# Five-Minute Demo & Pitch — PayState Bridge

## Core story

> A customer pays ₹999, their account looks debited, but the merchant has no order. The dangerous response is “please pay again.” PayState Bridge resolves the payment state before retrying, so the merchant either restores the existing order, sends one verified-failure recovery link, or safely escalates.

## Demo data

### Merchant

**FitCart India** — fictional D2C fitness-accessories merchant.

### Order

```text
Order: ORD-1042
Item: AeroFlex Resistance Band Set
Amount: ₹999
Original payment reference: SYN-PAY-101
Customer report reference: SYN-UTR-20260830-001
```

All names, references, screenshots, and amounts are synthetic.

## Video script

| Time | Screen | Narrative |
|---|---|---|
| 0:00–0:25 | Title and simple gap diagram: customer app → bank/NPCI → gateway → merchant | “When a UPI payment looks stuck, customers are often told to pay again. But a payment can still settle later. That turns one unclear payment into a duplicate payment, refund chase, and loss of trust.” |
| 0:25–0:50 | Problem card with customer message: “PhonePe deducted ₹999 but no order. Should I pay again?” | “Existing apps, banks, NPCI, and gateways all have valid roles. The merchant still needs one immediate answer: should we ask this customer to pay again?” |
| 0:50–1:40 | Case A: event timeline; merchant order `PAYMENT_PENDING`; gateway event `pending` | “PayState Bridge separates customer-reported evidence from merchant/gateway evidence. The customer report matters, but it cannot prove settlement. Gateway status is pending, so the agent applies the stopping rule: do not retry.” |
| 1:40–2:00 | Customer reply + audit card | “The customer gets a clear response: ‘We are verifying your payment. Please do not pay again.’ The audit trail records why that decision was made and when to recheck.” |
| 2:00–2:40 | Simulated later `captured` event; order still missing | “Later, the gateway reports captured. Instead of generating another payment link, PayState Bridge finds the matching unpaid order and reconciles it. The merchant recovers the original sale without asking the customer for another payment.” |
| 2:40–3:20 | Case B: final `failed` event; recovery permit → Razorpay Test Mode link | “Only when the original payment has verified final failure does the recovery action unlock. The system creates exactly one Razorpay Test Mode payment link. Clicking twice returns the same link because recovery is idempotent.” |
| 3:20–3:50 | Case C: two captured payments; duplicate review screen | “If two successful payments map to one order, PayState Bridge does not blindly refund. It opens a human-approved duplicate review with both payment references and a full audit trail.” |
| 3:50–4:15 | Case D: screenshot/text cannot be verified; evidence packet | “If sources conflict, the product does not guess. It creates an outcome-unknown evidence packet with order/payment references and the official route guidance. It does not claim bank access or guaranteed recovery.” |
| 4:15–4:40 | One graceful failure: malformed synthetic screenshot / model timeout | “Here the screenshot extractor fails. The final state is outcome unknown, and the recovery-link button stays unavailable. AI extraction cannot override payment truth.” |
| 4:40–5:00 | Evaluation dashboard, repository, closing | “On our held-out synthetic batch we measure state accuracy, captured-payment recovery, duplicate detection, simulated GMV recovered, and the critical safety metric: unsafe retry-link rate. The target is zero. PayState Bridge has one rule: resolve before retry.” |

## Essential screens

1. Merchant case queue
2. Case evidence timeline with source labels
3. Decision panel: state / action / why / prohibited action
4. Customer-safe reply
5. Captured-unlinked order reconciliation
6. Test Mode recovery-link panel
7. Duplicate review
8. Evidence packet / outcome unknown
9. Evaluation dashboard

## Failure cases to show

### Failure 1 — pending means no retry

```text
Gateway status: pending
Action: DO_NOT_RETRY
Recovery link: disabled
```

### Failure 2 — screenshot is not proof

```text
Customer screenshot says success
Gateway evidence unavailable or contradictory
Action: OUTCOME_UNKNOWN → human/evidence packet
```

### Failure 3 — invalid webhook

```text
Webhook signature invalid
Action: reject event; no order state change
```

## Metrics screen

Do not invent results. Show actual values after `make eval`:

- state classification accuracy;
- captured-unlinked recovery recall;
- duplicate-success detection recall;
- verified recovery-link precision;
- simulated GMV recovered;
- evidence-packet completeness;
- unsafe retry-link rate;
- false-positive human-review cost.

Say this explicitly:

> “All incidents, payment references, screenshots, and GMV values are synthetic. These are controlled reliability metrics, not a claim of real bank recovery or live merchant revenue.”

## Panel questions and answers

| Question | Answer |
|---|---|
| Why is this not just a complaint tracker? | Complaint portals are after-the-fact and consumer-side. This is merchant-side: it decides whether the merchant should retry, reconcile, or wait before creating a new payment action. |
| Why is AI needed? | AI structures untrusted customer text/synthetic screenshots and drafts bounded communication. Deterministic merchant/gateway evidence decides money actions. |
| Can this access PhonePe or bank status? | No. v0 intentionally does not claim that. It uses merchant/gateway/Test Mode evidence and correctly marks unknown state when it lacks proof. |
| Why Track 03? | It detects payment degradation, diagnoses state, recovers captured-but-unlinked revenue or verified failure, and stops unsafe retries with audit trail. |
| What is revenue recovered? | Simulated GMV from captured payments reconciled to orders and verified failed-payment recovery links. It is labelled simulated. |
| What if customer paid the wrong person? | A successful wrong-recipient transfer cannot be automatically reversed; recipient consent and official bank/NPCI route matter. The product provides evidence/guidance only. |
| Why not just use an idempotency key? | It stops an identical API retry. This handles merchant decision-making when a customer may retry through another app/link because the original outcome is unclear. |

## Closing line

> “Payment apps can tell customers where to complain. PayState Bridge helps merchants avoid creating the complaint in the first place: resolve before retry.”
