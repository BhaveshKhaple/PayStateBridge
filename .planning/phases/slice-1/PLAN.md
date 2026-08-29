# Slice 1 — Recovery State Engine

**Phase goal:** Full deterministic payment-state engine with database, case lifecycle, audit trail, and a working merchant console showing the PENDING → DO_NOT_RETRY case.
**Date target:** 31/08/2026
**Tasks:** S1-01, S1-02, S1-03, S1-04, S1-05
**Cut line:** No LLM/Gemini calls. No Razorpay calls. Deterministic logic only.

## Acceptance criteria (all must pass)

- [ ] Seeded incidents load into SQLite via async SQLAlchemy
- [ ] Every evidence record has a `source_type` field
- [ ] Money stored as integer paise everywhere
- [ ] Same input events → same state/action (deterministic)
- [ ] PENDING and OUTCOME_UNKNOWN never expose CREATE_RECOVERY_PERMIT action
- [ ] CAPTURED_UNLINKED produces RECONCILE_ORDER
- [ ] WRONG_RECIPIENT never claims auto-recovery
- [ ] Audit timeline shows: source type, decision, action, timestamp, reason codes
- [ ] Illegal state transitions are rejected with 422
- [ ] Merchant console (Next.js) shows PENDING case with DO_NOT_RETRY decision
- [ ] Recovery-link button absent/disabled for PENDING cases
- [ ] Evidence timeline shown on case detail page
- [ ] Works at 360px mobile width
- [ ] `pytest` passes all 20 dev incident fixtures + policy unit tests
- [ ] `npm run build` passes

## Tasks

### S1-01 — Trust-boundary schemas + database
SQLAlchemy async models + Alembic + DB session + case/evidence/audit CRUD

### S1-02 — Deterministic classifier (integrate with DB)
Classifier already exists in `app/domain/classifier.py` — wire it to the service layer

### S1-03 — Case lifecycle + audit trail
Legal state transitions, append-only audit events, state machine

### S1-04 — Merchant case console — pending flow
Next.js pages: /cases list + /cases/[id] detail with evidence timeline + safe customer reply

### S1-05 — Core policy and API tests
Unit tests for all 20 dev fixtures + policy matrix + illegal transition tests + API integration tests
