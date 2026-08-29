# Submission — Razorpay AI Buildathon Track 03

**Project:** PayState Bridge  
**Track:** 03 — AI Revenue Recovery  
**Builder:** Bhavesh Khaple  
**Repository:** https://github.com/BhaveshKhaple/PayStateBridge  
**Deadline:** 05/09/2026

## What was built

A merchant-side payment ambiguity resolver. Given a customer report of a debited payment with no order confirmation, PayState Bridge determines the safest next action from authoritative gateway evidence — before asking the customer to pay again.

## Track 03 requirements

| Requirement | Implementation |
|---|---|
| Payment degradation detection | 7-state classifier from gateway events |
| Root cause diagnosis | Deterministic evidence precedence rules |
| Bounded recovery action | Reconcile / Test Mode link / evidence packet |
| Simulated GMV measurement | Eval runner with captured-unlinked + failed recovery |
| Stopping rules | PENDING/UNKNOWN → DO_NOT_RETRY enforced everywhere |
| Audit trail | Append-only AuditEvent on every transition |

## Key files for reviewers

| File/Dir | What to look at |
|---|---|
| `apps/api/app/domain/classifier.py` | Core deterministic policy engine |
| `apps/api/app/domain/state_machine.py` | Legal state transitions |
| `apps/api/app/services/` | Recovery workflows (reconcile, permit, link, packet) |
| `apps/api/app/integrations/` | Gemini extractor + Razorpay adapter + FakeProvider |
| `apps/api/tests/` | 70+ tests including safety invariants |
| `apps/api/app/evals/runner.py` | Evaluation runner with safety gate |
| `data/incidents/` | 60 synthetic incidents (36 dev + 24 heldout) |
| `docs/HLD.md` | High-level design |
| `docs/LLD.md` | Low-level design per module |
| `docs/TEST_CASES.md` | 75+ test case specifications |

## Run the demo

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) and [docs/SETUP.md](docs/SETUP.md).

## Limitations

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the complete, honest out-of-scope list.

## Simulated GMV disclaimer

All GMV figures are simulated from synthetic incidents only. No real money was processed, recovered, or refunded. Razorpay Test Mode was used exclusively.
