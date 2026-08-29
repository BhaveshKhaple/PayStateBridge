# Tech Stack — PayState Bridge

**Research date:** 30/08/2026. Re-check package versions before installation; this file explains choices, not permanent version pins.

## The simple stack

```text
VS Code + Antigravity + GSD
        ↓
Next.js + TypeScript     → merchant-support dashboard
        ↓ HTTP
FastAPI + Python         → recovery state machine and API
        ↓
SQLite                    → synthetic orders, payment evidence, cases, audit log
        ↓
Razorpay Test Mode        → one bounded recovery payment link
        ↓
Gemini (optional)        → read structured fields from synthetic message/screenshot
```

## What each part does

| Part | Tool | Plain-language responsibility | Why we use it |
|---|---|---|---|
| Code workspace | VS Code + Google Antigravity + GSD | Lets Bhavesh plan, build, test, and commit one slice at a time. | Already Bhavesh’s workflow; GSD keeps work small and verified. |
| Merchant dashboard | Next.js + TypeScript | Shows customer payment cases, evidence timeline, decision, recovery action, and audit log. | Good mobile/web UI and easy browser testing. |
| Backend | FastAPI + Python | Holds all rules: pending means no retry; failed can unlock one recovery link; captured payment can restore order. | Pydantic validation and Python fixtures are ideal for safe, explicit state logic. |
| Database | SQLite | Stores synthetic orders, payment events, cases, recovery actions, and audit events in one local file. | Zero server setup for solo prototype; can migrate to Postgres later. |
| Rules | Pure Python functions + Pydantic | Makes final decision from merchant/gateway evidence, not AI opinion. | Money actions must be predictable and testable. |
| AI extraction | Gemini structured output + optional image understanding | Reads untrusted customer text or synthetic mock screenshot into fields: amount, claimed status, UTR-like reference. | Meaningful AI use, but it has no payment authority. |
| Payment action | Razorpay Test Mode Payment Links | Creates a single new link only after original payment is verified failed. | Directly demonstrates Track 03 recovery action without real money. |
| Event proof | Razorpay callback/webhooks + HMAC | Confirms Test Mode payment event is genuine; rejects forged/duplicate events. | Customer screenshot/browser redirect is not payment truth. |
| Tests | Pytest + Playwright | Pytest checks rules; Playwright checks merchant UI in real browser. | Prevents unsafe recovery regressions. |
| CI | GitHub Actions | Runs lint, type checks, tests, evaluation, and build on every push/PR. | Gives reviewer reproducible evidence. |

## Install requirements

| Install now | Needed for | Required at start? |
|---|---|---:|
| Git | version control / GitHub | Yes |
| Node.js LTS (22.x or newer supported LTS) | Next.js dashboard | Yes |
| Python 3.12+ | FastAPI backend | Yes |
| VS Code + Antigravity extension | development workflow | Yes |
| GSD workflow | plan → execute → verify slices | Yes if Bhavesh uses it |
| Gemini API key | live extractor only | No — use fake extractor first |
| Razorpay Test Mode keys | recovery-link proof | No — needed only in Slice 4 |
| Public staging/tunnel | live webhook delivery proof | No — needed only after core works |

## Why we deliberately avoid heavy tools

- **No vector DB/RAG:** orders and payment events are exact relational records, not documents to semantically search.
- **No fine-tuning:** structured extraction plus validation is enough for a 6-day prototype.
- **No multi-agent system:** one audited state machine is safer than multiple agents passing payment authority. 2026 winners used specialists *behind* a fence; Track 03 clones already overuse swarms.
- **No blockchain:** normal audit records are enough for a portfolio prototype.
- **No direct bank/NPCI integration:** not publicly available to a student and would be unsafe to claim.
- **No Google ADK as the product:** ADK 2.0 (`google-adk`) is a strong optional *extractor* later. Making money tools callable from an ADK/Antom-style payment agent is the anti-pattern. See `HACKATHON_AND_STACK_RESEARCH.md`.
- **No LangGraph / LangChain / CrewAI / LlamaIndex:** crowded, default-unsafe for payment writes, and they do not help the pending-vs-retry problem.
- **No Reserve Pay / Autopay rebuild:** those are live Razorpay products. We sit *before* a second charge, not inside SBMD or mandate retry.

## What “AI” does and does not do

```text
AI MAY:
- extract fields from customer text/synthetic screenshot
- identify missing information
- draft a cautious customer reply

AI MAY NOT:
- declare payment captured/failed
- create recovery permit
- create payment link
- issue refund
- override merchant/gateway evidence
```

## Minimum local commands (target)

```bash
# frontend
cd apps/web && npm install && npm run dev

# backend
cd apps/api && python -m venv .venv
# activate environment, then install project dependencies
pytest

# whole project checks
npm run lint
npm run typecheck
pytest
npm run build
```

Exact commands will be finalized in Slice 0 after the project is scaffolded.
