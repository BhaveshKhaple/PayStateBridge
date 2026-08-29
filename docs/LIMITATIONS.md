<!-- generated-by: gsd-doc-writer -->
# PayState Bridge — Honest Limitations

> This document describes what the prototype can and cannot do. It is intentional and complete. Read it before interpreting any demo output, metric, or evidence packet.

---

## What This Prototype Can Do

The following capabilities are implemented and tested in this repository:

**Deterministic payment-state classification**
The classifier (`app/domain/classifier.py`) correctly identifies seven payment states (PENDING, FAILED, CAPTURED_UNLINKED, DUPLICATE_SUCCESS, OUTCOME_UNKNOWN, WRONG_RECIPIENT, UNAUTHORIZED) from synthetic gateway events and merchant order data. It applies gateway-evidence-wins precedence. All classification rules are explicit, auditable Python — no model inference is involved.

**Safety enforcement: no retry link for unresolved payments**
The recovery permit service blocks all states except FAILED from receiving a recovery permit. The config validation blocks non-demo `APP_ENV` values and `rzp_live_` key prefixes at startup. These checks are verified by 12+ safety-category tests. The CI pipeline fails if any fixture with PENDING or OUTCOME_UNKNOWN state produces a `CREATE_RECOVERY_PERMIT` action.

**Order reconciliation for captured-but-unlinked payments**
The reconcile service applies exact amount, reference, and 30-minute time-window matching to link a captured gateway payment to an unpaid merchant order. It raises a distinct `AmbiguousMatchError` when multiple captured payments exist, routing those cases to human review rather than making an automated guess.

**Duplicate payment detection and review workflow**
When two or more captured events map to one order, the classifier labels the case `DUPLICATE_SUCCESS` and the duplicate review service records both payment IDs for merchant review. No refund is ever triggered automatically. The service module contains no Razorpay or refund import.

**Injection-safe AI evidence extraction**
Both `FakeEvidenceExtractor` and `GeminiEvidenceExtractor` run injection pattern detection before processing any input. Eight injection regex patterns are checked. Blocked input returns `FAILED` status with `fallback_action=OUTCOME_UNKNOWN`. The Gemini extractor additionally blocks injection before making any API call. All extracted output is tagged `untrusted_customer_provided` by the Pydantic schema and cannot override gateway evidence.

**Structured evidence packets for unresolvable cases**
For OUTCOME_UNKNOWN and WRONG_RECIPIENT cases, the evidence packet service assembles all evidence references, labels each by trust level, and provides the official UPI/NPCI dispute escalation path. No packet promises recovery, a refund timeline, or bank action.

**Razorpay Test Mode integration (optional)**
When a `rzp_test_` key is configured, the `RazorpayTestModeProvider` creates a real Test Mode payment link from a valid `RecoveryPermit`. The webhook handler verifies HMAC on the raw body before parsing, deduplicates by `event_id`, and transitions the case to `RECOVERY_PAID_TEST` on `payment_link.paid`.

**Append-only audit trail**
Every state transition is recorded as an `AuditEvent` with prior state, new state, reason codes, and evidence IDs. No audit row is modified after insertion. The trail covers the full case lifecycle.

**Synthetic evaluation framework**
The repository contains a fixture-driven evaluation suite (`data/incidents/dev/`, `tests/test_fixtures.py`) with 34 development-split incidents at time of writing. The heldout split target is 24 incidents. The CI safety gate asserts `unsafe_retry_link_rate == 0` across all fixtures.

---

## What This Prototype Cannot Do

**Access real payment network data**
This prototype has no connection to NPCI, the UPI switch, any bank's core banking system, Razorpay's live settlement data, PhonePe's internal API, or Google Pay's internal API. All payment events used in classification are either synthetic fixtures (`data/incidents/`) or Razorpay Test Mode events. The prototype cannot read a real transaction's status, real UTR, or real settlement state.

**Verify a real customer screenshot**
The Gemini extractor processes synthetic screenshot fixture names, not actual image files or real app screenshots. Even if a real screenshot were submitted, the extractor output would be tagged `untrusted_customer_provided` and would not change the payment state classification. The system cannot authenticate that a screenshot is genuine.

**Execute a refund**
There is no refund API integration. The duplicate review service records a merchant approval decision and writes an audit event. The merchant must process any refund manually through their Razorpay dashboard or bank. This is intentional — refund execution requires real financial authority and merchant approval beyond what this prototype implements.

**File a complaint or submit a dispute on behalf of anyone**
The evidence packet provides the official escalation route (PhonePe Help, bank customer care, pgms.npci.org.in). It does not submit a complaint. The prototype has no integration with NPCI's PGMS, RBI's CMS, or any bank's dispute portal.

**Guarantee payment recovery or refund timing**
Every customer-facing message in the system is reviewed to exclude the words "guarantee", "will refund", and "bank will". Recovery outcomes depend on the merchant's bank, NPCI processes, and external party cooperation. This prototype can identify the correct next action; it cannot enforce it.

**Handle multiple merchants or production authentication**
The v0 prototype is scoped to one synthetic D2C merchant. There is no multi-tenant data model, no production-grade authentication (API keys, OAuth, session management), and no row-level access control. The system is not appropriate for production use.

**Operate in any environment other than `APP_ENV=demo`**
The startup config validation calls `sys.exit(1)` if `APP_ENV` is anything other than `"demo"`. This is a hard barrier to prevent accidental live-mode deployment.

**Perform real UTR verification**
UTR-like references in fixtures use synthetic patterns like `SYN-UTR-20260830-001`. The system cannot query NPCI or any bank to verify whether a real UTR corresponds to a completed settlement.

---

## Synthetic Data Disclaimer

All payment incidents, orders, payment events, UTR-like references, and customer messages in this repository are synthetic. They were created specifically for the Razorpay AI Buildathon.

- No real customer data, bank statement, PhonePe export, Google Pay export, or Razorpay transaction data is stored in this repository.
- No real merchant account data is used.
- UTR-like references follow the pattern `SYN-UTR-YYYYMMDD-NNN` and are not valid NPCI references.
- Simulated GMV figures (the `simulated_gmv_paise` field on each incident) are labelled `SIMULATED` in all evaluation output. They do not represent real merchant revenue.
- The dataset of 60 total incidents (36 dev + 24 heldout) is small by production ML standards. Accuracy figures derived from this dataset should not be generalised to real-world payment failure distributions.

---

## Test Mode Disclaimer

When `RAZORPAY_KEY_ID` is set to a `rzp_test_` key:

- Payment links are created in Razorpay Test Mode. No real money is charged or moved.
- Test Mode payment links are subject to Razorpay's Test Mode limits (documented as 30 links per business at time of writing). All automated tests use `FakePaymentProvider` to avoid consuming this quota.
- Webhook events received and processed are Test Mode events only. They have no financial effect.
- The `RecoveryPermit` schema has `environment: Literal["test"]`. It is impossible to issue a permit without this label in the current implementation.

---

## AI Boundary Disclaimer

Gemini is used in this prototype only to parse unstructured customer text into typed fields. It is not used to:

- Decide the payment state (PENDING, FAILED, CAPTURED_UNLINKED, etc.)
- Determine what recovery action to take
- Create, cancel, or modify payment links
- Authorise or approve any financial operation

The `ExtractedCustomerReport` Pydantic model has no `payment_state`, `recovery_action`, `create_payment_link`, or equivalent field. Any field returned by the model that is not in the schema is silently dropped before the result is stored. All model output is tagged `untrusted_customer_provided` and is treated as supplementary context, not authoritative evidence.

Injection patterns are blocked before any API call is made to Gemini. The extractor returns `FAILED` status and the classifier falls back to `OUTCOME_UNKNOWN` when injection is detected.

---

## Explicit Out-of-Scope Items

| Capability | Status | Notes |
|---|---|---|
| Direct NPCI switch access | Out of scope | No public student API; no authority to read live UPI state |
| Bank-core access | Out of scope | Requires bilateral banking agreement |
| PhonePe private API | Out of scope | No public access |
| Google Pay private API | Out of scope | No public access |
| Live money refunds | Out of scope | Requires real merchant financial authority; v0 creates a review record only |
| Autonomous complaint filing | Out of scope | NPCI PGMS, RBI CMS, and bank portals are external regulated systems |
| Forced reversal of wrong-recipient transfers | Out of scope | Merchant has no legal authority to reverse a completed UPI transfer to a third party |
| Real UTR verification | Out of scope | Requires NPCI or bank query access |
| Real screenshot image analysis | Out of scope | Gemini receives fixture names, not actual image bytes from customers |
| Multi-tenant support | Out of scope | Single synthetic merchant only |
| Production-grade authentication | Out of scope | No API key management, OAuth, or session security |
| Live mode payment processing | Out of scope | Blocked at startup config level; `rzp_live_` keys rejected |
| Guaranteed SLA on recovery | Out of scope | External parties (bank, NPCI, recipient) control actual resolution time |
| Consumer complaint chatbot | Out of scope | NPCI UPI Help already provides status and grievance capability for consumers |
