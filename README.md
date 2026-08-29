# PayState Bridge — Build Kit

> **Track:** Razorpay AI Buildathon, Track 03 — AI Revenue Recovery  
> **Submission target:** 05/09/2026  
> **Maturity:** portfolio-grade merchant-side prototype using synthetic incidents and Razorpay Test Mode only

## One-line project

**PayState Bridge resolves a customer’s ambiguous payment before a merchant asks them to pay again—preventing duplicate payments, recovering captured-but-unlinked orders, and creating the next safe action with evidence.**

## The real problem

A customer pays with PhonePe, Google Pay, a bank app, or a Razorpay checkout. Their account is debited, but the merchant does not yet see a completed order. The customer is told to try again, pays a second time, and the first payment later succeeds or reverses slowly.

The customer then navigates a fragmented path across the app, bank, merchant, NPCI, and sometimes RBI. Each party sees only part of the payment. The merchant has the most immediate ability to stop a harmful retry, but most merchant checkouts cannot explain the payment state or choose a safe recovery action.

> **Resolve before retry.** Never generate a replacement payment link while the first payment is pending or outcome-unknown.

## v0 scope

- One synthetic D2C merchant and one Razorpay Test Mode checkout adapter.
- Synthetic payment events, UTR-like references, customer messages, and incident screenshots.
- Deterministic case classifier: `PENDING`, `FAILED`, `CAPTURED_UNLINKED`, `DUPLICATE_SUCCESS`, `OUTCOME_UNKNOWN`, `WRONG_RECIPIENT`, `UNAUTHORIZED`.
- Bounded merchant actions: wait/reconcile, link an existing captured payment to an order, generate one replacement Test Mode link only after verified failure, create a human-approved duplicate-refund review, or generate an evidence packet.
- Customer-facing safe reply: **do not pay again** while the prior outcome is unresolved.
- Audit timeline, held-out synthetic evaluation set, and CI safety gate.

## Explicitly out of scope

- Direct NPCI switch access, bank-core access, PhonePe/Google Pay private APIs, live-money settlement, autonomous complaint filing, forced reversal of wrong-recipient transfers, refund execution without merchant approval, and any claim that the product can guarantee recovery.
- A generic consumer complaint chatbot. NPCI already offers UPI Help with status and grievance capability.

## Why Track 03

PayState Bridge implements the Buildathon's stated loop:

```text
payment degradation → root cause → bounded recovery action
```

It measures simulated GMV recovered from captured-but-unlinked payments and verified replacement payments, while measuring the critical safety metric: **unsafe retry-link rate must be zero**.

## Documentation map

1. [Problem & product requirements](docs/PRD.md)
2. [India payment domain primer](docs/PAYMENT_DOMAIN_PRIMER.md)
3. [Architecture & tech stack](docs/ARCHITECTURE.md)
4. [API, data, and state contracts](docs/API_AND_DATA_CONTRACTS.md)
5. [RAD delivery plan](docs/BUILD_PLAN.md)
6. [Evaluation, security, and operations](docs/EVALUATION_AND_SAFETY.md)
7. [Razorpay Test Mode runbook](docs/RAZORPAY_TEST_MODE_RUNBOOK.md)
8. [Competitor and alternatives study](docs/COMPETITOR_STUDY.md)
9. [2026 hackathon-win patterns, Track 03 field, ADK and libraries](docs/HACKATHON_AND_STACK_RESEARCH.md)
10. [Demo and five-minute pitch](docs/DEMO_AND_PITCH.md)
11. [Submission playbook](docs/SUBMISSION_PLAYBOOK.md)
12. [Research and decision log](docs/RESEARCH_AND_DECISIONS.md)

## Architecture in one line

**Next.js merchant console → FastAPI modular monolith → SQLite/Postgres → deterministic payment-state and recovery policy engine → Razorpay Test Mode adapter/webhook verifier, with Gemini used only to structure customer-provided text or synthetic screenshots.**

## Start point

Begin with **Slice 0 / B0-01** in the tracker: repository skeleton, synthetic event simulator, and a single payment-ambiguity case that reaches a safe `DO_NOT_RETRY` result.
