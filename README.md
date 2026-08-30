# PayState Bridge

> **Razorpay AI Buildathon · Track 03 — AI Revenue Recovery**  
> Submission deadline: 05/09/2026 · Solo build by Bhavesh Khaple

---

## Important disclaimers

- **Synthetic data only.** All payment events, UTR references, screenshots, and customer messages are synthetic. No real bank, UPI, NPCI, or PhonePe/Google Pay data is used.
- **Razorpay Test Mode only.** Recovery links use `rzp_test_` credentials exclusively. No real money is charged or refunded.
- **Portfolio prototype.** All recovered GMV figures are simulated. This is a merchant-side decision-support tool, not a live payment processor.

---

## What it does

A customer pays with PhonePe or Google Pay. Their account shows a debit but the merchant has no confirmed order. The harmful default is: *"please pay again."* That creates a duplicate charge.

**PayState Bridge stops that.** It determines the safest next action from merchant/gateway evidence before a new payment link is created.

```
ambiguous payment
→ classify from gateway evidence (not customer claim)
→ PENDING / UNKNOWN → DO NOT RETRY
→ CAPTURED_UNLINKED → link to order (no new charge)
→ FAILED (verified) → one Test Mode recovery link
→ DUPLICATE → human review (no auto-refund)
```

**Core law:** Never generate a replacement payment link while the first payment is `PENDING` or `OUTCOME_UNKNOWN`.

---

## Payment states handled

| State | Merchant action | Customer message |
|---|---|---|
| `PENDING` | Do not retry · wait | "Please do not pay again while we verify." |
| `FAILED` | One Test Mode recovery link | "First payment verified failed — here is a fresh link." |
| `CAPTURED_UNLINKED` | Link payment to order | "Your payment is confirmed — restoring your order." |
| `DUPLICATE_SUCCESS` | Human refund review | "Two payments found — our team is reviewing." |
| `OUTCOME_UNKNOWN` | Evidence packet + escalation | "Cannot confirm outcome — do not retry." |
| `WRONG_RECIPIENT` | Official bank/NPCI route | "Cannot reverse this transfer — use official process." |
| `UNAUTHORIZED` | Security escalation | "Contact your bank immediately." |

---

## Live deployment

PayState Bridge deploys as a Vercel (web) + Railway/Render (API) pair. See **[DEPLOY.md](DEPLOY.md)** for the full step-by-step guide, including env vars, CORS wiring, and the optional Razorpay Test Mode webhook.

Live demo: _(add Vercel URL after deploy)_

---

## Quick start (local)

### Prerequisites
- Python 3.12+
- Node.js 22+
- Git

### 1. Clone and configure

```bash
git clone https://github.com/BhaveshKhaple/PayStateBridge.git
cd PayStateBridge
cp .env.example .env
# Edit .env: APP_ENV=demo (required)
# Optionally add GEMINI_API_KEY and RAZORPAY_KEY_ID (rzp_test_ only)
```

### 2. API setup

```bash
cd apps/api
python -m venv .venv

# Windows
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m app.db.seed   # loads 36 synthetic incidents
.venv\Scripts\uvicorn app.main:app --reload --port 8000

# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

### 3. Web setup

```bash
cd apps/web
npm install
npm run dev
```

### 4. Open

| URL | Purpose |
|---|---|
| http://localhost:3000 | Merchant support console |
| http://localhost:3000/cases | All synthetic cases |
| http://localhost:8000/docs | API docs (Swagger) |
| http://localhost:8000/health | Health check |

---

## Run tests

```bash
cd apps/api

# Unit + integration tests
pytest --tb=short -q

# Evaluation safety gate (must exit 0)
python -m app.evals.runner --split dev
python -m app.evals.runner --split heldout

# Full evaluation report
python -m app.evals.runner --split all --json-out eval_report.json
```

---

## Architecture

```
Next.js merchant console
    ↓ HTTP
FastAPI modular monolith
    ├── Deterministic classifier (gateway evidence wins)
    ├── Case lifecycle + append-only audit trail
    ├── Recovery workflows (reconcile / duplicate review / evidence packet)
    ├── AI intake (Gemini optional — extracts fields only, never decides state)
    └── Razorpay Test Mode adapter (FakeProvider in CI)
    ↓
SQLite (synthetic orders, payments, cases, audit events)
```

Full design docs: [HLD](docs/HLD.md) · [LLD](docs/LLD.md) · [Test Cases](docs/TEST_CASES.md) · [Limitations](docs/LIMITATIONS.md)

---

## Project structure

```
paystate-bridge/
  apps/
    web/                    # Next.js merchant console
    api/                    # FastAPI recovery engine
      app/
        domain/             # classifier, state machine
        services/           # case, reconcile, permit, recovery link, evidence packet
        integrations/       # Gemini extractor, Razorpay adapter, FakeProvider
        db/                 # SQLAlchemy models, seed
        evals/              # evaluation runner
      tests/
  data/
    incidents/dev/          # 36 synthetic dev incidents
    incidents/heldout/      # 24 sealed heldout incidents
  docs/                     # HLD, LLD, PRD, TEST_CASES, LIMITATIONS, BUILD_PLAN
  .github/workflows/ci.yml  # lint + typecheck + pytest + eval safety gate
```

---

## CI / GitHub Actions

Every push to `main` runs:
1. Python tests (`pytest` — no API keys required)
2. Evaluation safety gate — dev split (exits 1 if any unsafe retry-link)
3. Evaluation safety gate — heldout split
4. Next.js lint + typecheck + build

---

## Documentation

| Doc | Purpose |
|---|---|
| [PRD](docs/PRD.md) | Product requirements and acceptance criteria |
| [BUILD_PLAN](docs/BUILD_PLAN.md) | Six-day delivery plan with slice breakdown |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Architecture decisions and trust boundaries |
| [HLD](docs/HLD.md) | High-level design with component diagram |
| [LLD](docs/LLD.md) | Low-level design per module |
| [TEST_CASES](docs/TEST_CASES.md) | 75+ test case specifications |
| [LIMITATIONS](docs/LIMITATIONS.md) | Honest scope and out-of-scope list |
| [API_AND_DATA_CONTRACTS](docs/API_AND_DATA_CONTRACTS.md) | Pydantic schemas, state machine, API routes |
| [EVALUATION_AND_SAFETY](docs/EVALUATION_AND_SAFETY.md) | Eval metrics, safety gates, guardrails |
| [COMPETITOR_STUDY](docs/COMPETITOR_STUDY.md) | Alternatives analysis |
| [DEMO_AND_PITCH](docs/DEMO_AND_PITCH.md) | Five-minute demo script |
| [SUBMISSION_PLAYBOOK](docs/SUBMISSION_PLAYBOOK.md) | Submission checklist |

---

## Track 03 requirements mapping

| Requirement | PayState Bridge |
|---|---|
| Detect revenue at risk | Classifies 7 payment states from gateway + order evidence |
| Diagnose root cause | Deterministic classifier with evidence precedence rules |
| Execute bounded recovery | Reconcile order / Test Mode link / evidence packet |
| Show money recovered | Eval runner reports simulated GMV (labelled synthetic) |
| Stopping rules | PENDING/UNKNOWN → DO_NOT_RETRY enforced at every layer |
| Audit trail | Append-only AuditEvent on every state transition |

---

*Built with Next.js · FastAPI · SQLite · Gemini (optional) · Razorpay Test Mode*  
*Razorpay AI Buildathon 2026 · Track 03 · Bhavesh Khaple*
