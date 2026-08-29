# Slice 0 — Bootstrap

**Phase goal:** Working repo skeleton that a fresh clone can run, with a working synthetic PENDING → DO_NOT_RETRY case.  
**Date:** 30/08/2026  
**Tasks:** B0-01, B0-02, B0-03  
**Cut line:** No LLM/Razorpay yet.

## Acceptance criteria (all must pass)

- [ ] Fresh clone shows documented folder structure
- [ ] README says "Synthetic data / Test Mode only" prominently
- [ ] `.env.example` has variable names only, zero values/secrets
- [ ] `npm run dev` (web) starts on port 3000
- [ ] `uvicorn` (api) starts on port 8000, `GET /health` → `{"status":"healthy"}`
- [ ] `npm run lint` passes
- [ ] `npm run typecheck` passes
- [ ] `pytest` passes (placeholder tests)
- [ ] `npm run build` passes
- [ ] Seed command loads 20+ synthetic incidents
- [ ] Every incident is visibly synthetic (no real UTR, no real account numbers)
- [ ] PENDING fixture always → DO_NOT_RETRY (no recovery link provider called)

---

## Task B0-01 — Repository skeleton

### Files to create

```
.env.example
.gitignore
package.json              (root workspace)
apps/web/package.json
apps/web/tsconfig.json
apps/web/next.config.ts
apps/web/app/layout.tsx
apps/web/app/page.tsx
apps/api/pyproject.toml
apps/api/requirements.txt
apps/api/app/__init__.py
apps/api/app/main.py
apps/api/tests/__init__.py
data/incidents/dev/.gitkeep
data/incidents/heldout/.gitkeep
data/screenshots/.gitkeep
docs/                     (already exists)
.github/workflows/ci.yml
```

### Commit message
`feat(bootstrap): B0-01 — repo skeleton, folder structure, env example`

---

## Task B0-02 — Runnable web/API skeleton

### Web (Next.js)

- `apps/web/app/layout.tsx` — root layout with metadata
- `apps/web/app/page.tsx` — landing page: project name, one-liner, "Synthetic data / Test Mode only" badge
- `apps/web/app/globals.css` — minimal Tailwind import
- `apps/web/tailwind.config.ts`
- `apps/web/postcss.config.mjs`

### API (FastAPI)

- `apps/api/app/main.py` — FastAPI app with `GET /health`
- `apps/api/app/api/__init__.py`
- `apps/api/app/api/health.py` — health router
- `apps/api/tests/test_health.py` — pytest: GET /health returns 200 + `{"status":"healthy"}`

### Root scripts (package.json)

```json
{
  "scripts": {
    "dev:web": "cd apps/web && npm run dev",
    "dev:api": "cd apps/api && uvicorn app.main:app --reload --port 8000",
    "lint": "cd apps/web && npm run lint",
    "typecheck": "cd apps/web && npx tsc --noEmit",
    "test": "cd apps/api && pytest",
    "build": "cd apps/web && npm run build"
  }
}
```

### Commit message
`feat(bootstrap): B0-02 — runnable Next.js + FastAPI skeleton, health endpoint`

---

## Task B0-03 — Synthetic incident simulator

### Schema (JSON per incident)

```json
{
  "incident_id": "INC-0001",
  "split": "dev",
  "scenario": "PENDING",
  "description": "Customer says PhonePe debited ₹999, no order confirmation",
  "merchant_order": {
    "order_id": "ORD-1042",
    "reference": "ORD-1042",
    "amount_paise": 99900,
    "status": "payment_pending",
    "created_at": "2026-08-30T08:00:00Z"
  },
  "gateway_events": [
    {
      "provider": "synthetic",
      "provider_payment_id": "SYN-PAY-20260830-001",
      "provider_order_id": "ORD-1042",
      "amount_paise": 99900,
      "status": "pending",
      "occurred_at": "2026-08-30T08:01:00Z",
      "raw_event_id": "SYN-EVT-20260830-001",
      "source": "gateway_event"
    }
  ],
  "customer_report": {
    "message": "My PhonePe account shows ₹999 deducted at 8:01 AM but I did not receive any order confirmation.",
    "amount_paise": 99900,
    "reported_status": "success",
    "utr_like_reference": "SYN-UTR-20260830-001",
    "occurred_at": "2026-08-30T08:01:00Z",
    "source": "customer_report"
  },
  "expected_state": "PENDING",
  "expected_action": "DO_NOT_RETRY",
  "simulated_gmv_paise": 0,
  "notes": "Gateway evidence is PENDING; customer report of success is untrusted. No recovery link must be created."
}
```

### 20 dev incidents to create

| ID | Scenario | Gateway status | Expected state | Expected action |
|---|---|---|---|---|
| INC-0001 | Pending — customer claims debit, gateway pending | pending | PENDING | DO_NOT_RETRY |
| INC-0002 | Pending — no gateway event yet | missing | OUTCOME_UNKNOWN | DO_NOT_RETRY |
| INC-0003 | Failed — gateway final failure | failed | FAILED | CREATE_RECOVERY_PERMIT |
| INC-0004 | Failed — customer claims success, gateway says failed | failed | FAILED | CREATE_RECOVERY_PERMIT |
| INC-0005 | Captured unlinked — webhook missed, order unpaid | captured | CAPTURED_UNLINKED | RECONCILE_ORDER |
| INC-0006 | Captured unlinked — amount matches, reference matches | captured | CAPTURED_UNLINKED | RECONCILE_ORDER |
| INC-0007 | Duplicate success — two captured events, one order | captured×2 | DUPLICATE_SUCCESS | OPEN_DUPLICATE_REVIEW |
| INC-0008 | Duplicate success — same amount, different payment IDs | captured×2 | DUPLICATE_SUCCESS | OPEN_DUPLICATE_REVIEW |
| INC-0009 | Outcome unknown — gateway missing, customer claims pending | missing | OUTCOME_UNKNOWN | DO_NOT_RETRY |
| INC-0010 | Outcome unknown — conflicting gateway events | conflict | OUTCOME_UNKNOWN | BUILD_EVIDENCE_PACKET |
| INC-0011 | Wrong recipient — customer sent to wrong UPI ID | captured_elsewhere | WRONG_RECIPIENT | OFFICIAL_ROUTE_GUIDANCE |
| INC-0012 | Wrong recipient — family member UPI, confirmed | captured_elsewhere | WRONG_RECIPIENT | OFFICIAL_ROUTE_GUIDANCE |
| INC-0013 | Unauthorized — customer did not initiate payment | unauthorized_claim | UNAUTHORIZED | SECURITY_ESCALATION |
| INC-0014 | Pending — mobile data cut during payment | pending | PENDING | DO_NOT_RETRY |
| INC-0015 | Failed — bank timeout, gateway failed | failed | FAILED | CREATE_RECOVERY_PERMIT |
| INC-0016 | Captured unlinked — order creation API timed out | captured | CAPTURED_UNLINKED | RECONCILE_ORDER |
| INC-0017 | Outcome unknown — amount mismatch between customer and gateway | conflict | OUTCOME_UNKNOWN | BUILD_EVIDENCE_PACKET |
| INC-0018 | Pending — customer paid twice claims (only one gateway event) | pending | PENDING | DO_NOT_RETRY |
| INC-0019 | Failed — expired session, gateway final failure | failed | FAILED | CREATE_RECOVERY_PERMIT |
| INC-0020 | Captured unlinked — order reference matches, 5-min window | captured | CAPTURED_UNLINKED | RECONCILE_ORDER |

### Seed script

`apps/api/app/db/seed.py` — loads all JSON from `data/incidents/dev/` into SQLite dev DB.

### Commit message
`feat(bootstrap): B0-03 — 20 synthetic dev incidents, seed script`

---

## Validation commands

```bash
cd apps/web && npm run lint
cd apps/web && npx tsc --noEmit
cd apps/api && pytest
cd apps/web && npm run build
```

## Non-goals for this slice

- No LLM/Gemini calls
- No Razorpay API calls
- No authentication
- No database migrations
- No Docker
