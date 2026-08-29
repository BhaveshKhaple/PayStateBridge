# PayState Bridge

**Track:** Razorpay AI Buildathon · Track 03 — AI Revenue Recovery  
**Deadline:** 05/09/2026  
**Builder:** Bhavesh Khaple (solo)  
**Repo:** https://github.com/BhaveshKhaple/PayStateBridge  
**Maturity:** Portfolio-grade prototype — synthetic incidents + Razorpay Test Mode only

## Mission

PayState Bridge resolves a customer's ambiguous payment before a merchant asks them to pay again — preventing duplicate payments, recovering captured-but-unlinked orders, and creating the next safe action with evidence.

**Core law:** Resolve before retry. Never generate a replacement payment link while the first payment is pending or outcome-unknown.

## Stack

- **Frontend:** Next.js 14 + TypeScript (merchant-support console)
- **Backend:** FastAPI + Python 3.12 (deterministic recovery state machine)
- **DB:** SQLite (SQLAlchemy async, migrations)
- **AI:** Gemini structured output — read only, no payment authority
- **Payments:** Razorpay Test Mode only — one bounded recovery link after verified failure
- **Tests:** Pytest + Playwright
- **CI:** GitHub Actions

## Payment states

PENDING · FAILED · CAPTURED_UNLINKED · DUPLICATE_SUCCESS · OUTCOME_UNKNOWN · WRONG_RECIPIENT · UNAUTHORIZED

## Hard product boundaries

- Synthetic data only. Test Mode only. Never live money.
- AI extracts fields from customer text/screenshots; deterministic code decides state and action.
- Never claim NPCI/PhonePe/GPay/bank-core access.
- Never create a recovery link while original payment is PENDING or OUTCOME_UNKNOWN.
- Never commit secrets, OTPs, UPI PINs, real UTRs, real screenshots.

## Phases

| Phase | Slice | Target date | Goal |
|---|---|---|---|
| slice-0 | Bootstrap | 30 Aug | Repo + folder structure + runnable skeleton + synthetic incidents |
| slice-1 | Recovery State Engine | 31 Aug | Deterministic classifier + case lifecycle + audit + merchant console |
| slice-2 | Recovery Workflows | 01 Sep | Captured-unlinked recovery + duplicate review + evidence packets |
| slice-3 | AI Evidence Intake | 02 Sep | Gemini extraction + safety tests |
| slice-4 | Razorpay Test Mode | 03 Sep | Recovery permit + Test Mode link + webhook verification |
| slice-5 | Evaluation & Quality | 04 Sep | 60 synthetic incidents + eval runner + CI + Playwright |
| slice-6 | Release | 05 Sep | Docs + demo + video + tag + submit |
