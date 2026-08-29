# Slice 2 — Recovery Workflows

**Phase goal:** Three safe recovery paths: captured-unlinked order reconciliation, duplicate-success review, and outcome-unknown/wrong-recipient evidence packets.
**Date target:** 01/09/2026
**Tasks:** S2-01, S2-02, S2-03
**Cut line:** No LLM. No Razorpay calls. Deterministic matching only.

## Acceptance criteria

- [ ] Captured-unlinked case → PAID_RECONCILED without new charge (exact amount+reference match)
- [ ] Ambiguous match → human review, not auto-reconcile
- [ ] Duplicate-success → opens DUPLICATE_REVIEW_OPEN, no refund API call
- [ ] Duplicate review shows both payment IDs, amounts, timestamps
- [ ] Operator can record approve/reject decision in audit trail
- [ ] OUTCOME_UNKNOWN → evidence packet (order ID, payment refs, timestamps, official route)
- [ ] WRONG_RECIPIENT → official-route guidance only, no recovery claim
- [ ] All generated customer replies pass "no unsupported promise" test
- [ ] New API routes: POST /v1/cases/{id}/reconcile, POST /v1/cases/{id}/duplicate-review/approve, GET /v1/cases/{id}/evidence-packet
- [ ] Reconcile requires exact policy match; ambiguous match returns 422
- [ ] Duplicate review case has two captured payment IDs, no refund provider call
- [ ] Evidence packet contains required fields and official route guidance
- [ ] UI shows reconcile/review/packet actions per state
- [ ] Tests: matching/non-matching amount+reference, duplicate detection, evidence packet fields
