# Submission Playbook — PayState Bridge

## 1. Entry positioning

**Track:** 03 — AI Revenue Recovery

### Title

# PayState Bridge
## Resolve before retry.

### Submission one-liner

> A merchant-side AI recovery agent that resolves ambiguous payment outcomes before asking a customer to pay again—preventing duplicate retries, reconciling captured-but-unlinked orders, and issuing one bounded recovery link only after verified failure.

### The non-negotiable qualification

> “This is a synthetic-data, Razorpay Test Mode prototype. It does not access PhonePe, Google Pay, NPCI, bank-core systems, or live customer payment data.”

## 2. Why this is different

| Common implementation | PayState Bridge |
|---|---|
| Customer sees payment unclear → merchant says “try again” | Merchant checks whether retry is safe before saying anything |
| Payment status dashboard | Recovery decision state machine with prohibited actions |
| Idempotency only | Handles human retry after ambiguous payment state and recovered order linkage |
| Back-office reconciliation later | Front-of-house support decision now |
| Complaint instructions | Merchant-side prevention + official-route evidence packet when merchant lacks authority |

## 3. Repository requirements

```text
README.md
LICENSE
apps/web
apps/api
data/incidents (synthetic only)
docs/PRD.md
docs/PAYMENT_DOMAIN_PRIMER.md
docs/ARCHITECTURE.md
docs/API_AND_DATA_CONTRACTS.md
docs/COMPETITOR_STUDY.md
docs/EVALUATION_AND_SAFETY.md
docs/RAZORPAY_TEST_MODE_RUNBOOK.md
docs/DEMO_AND_PITCH.md
.github/workflows/ci.yml
.env.example
EVAL_REPORT.md (generated from final tagged commit)
```

README first screen must answer:

1. What happens when a customer is asked to pay again while payment one is unresolved?
2. What does PayState Bridge do?
3. What evidence is trusted versus untrusted?
4. What is real Test Mode behavior versus synthetic/mock behavior?
5. How does a reviewer run tests/evaluation?
6. What are the hard limitations?

## 4. Evidence that reviewers should see

- A diagram of payment/app/bank/gateway/merchant fragmentation.
- A working `PENDING → DO_NOT_RETRY` flow.
- A captured-but-unlinked order reconciliation flow.
- A failed → single Test Mode recovery-link flow, if credentials/staging work.
- One invalid webhook or extraction failure safely routed to unknown/human review.
- Held-out evaluation report.
- CI pass on final commit.
- Clear synthetic-data/Test Mode labels.

## 5. Claims to avoid

Never say:

- “We recover UPI money.”
- “We are connected to NPCI/banks/PhonePe/Google Pay.”
- “We guarantee reversal/refund.”
- “We submit RBI/NPCI complaints.”
- “We tested on real users or real transactions.”
- “We eliminated duplicate transactions in production.”

Use these instead:

- “We prevent merchant-triggered retry while original payment outcome is unresolved.”
- “We reconcile synthetic/Razorpay Test Mode captured payment evidence to merchant order state.”
- “We create an official-route evidence packet when merchant-side evidence is insufficient.”
- “We measure controlled synthetic recovery behavior.”

## 6. Final pre-submit checklist

- [ ] Track 03 selected consistently on form, README, video, and pitch.
- [ ] Public GitHub repository works from fresh clone.
- [ ] Only synthetic data exists; no real UTR, screenshot, account, customer text, or payment record.
- [ ] No secret found in current files or git history.
- [ ] `make eval` / equivalent shows zero unsafe retry links.
- [ ] Held-out split labelled and not used in tuning.
- [ ] If Razorpay Test Mode works, callback/webhook verification shown; if not, limitation prominent.
- [ ] Demo video ≤5 minutes, showing safe failure—not only happy path.
- [ ] Every metric labelled “synthetic.”
- [ ] Final commit tagged and CI green.
- [ ] Submit before the deadline, not at the last minute.
