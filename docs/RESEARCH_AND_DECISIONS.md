# Research & Decision Log — PayState Bridge

**Research completed:** 30/08/2026. Re-check sources before implementation because help flows, limits, policies, and SDK behavior change.

## 1. Verified domain findings

| Finding | Primary / credible evidence | Project consequence |
|---|---|---|
| UPI payment complaints have a defined escalation path: TPAP/PSP app first, then PSP bank, user bank, NPCI, then relevant Ombudsman route. | [NPCI UPI dispute mechanism](https://www.npci.org.in/what-we-do/upi/dispute-redressal-mechanism) | Do not build a generic complaint portal or claim we replace NPCI. Build merchant-side pre-retry decision support. |
| NPCI already operates UPI Help with payment Q&A, status/grievance, and mandate support. | [NPCI UPI Help](https://upihelp.npci.org.in/) | Do not pitch “AI assistant for UPI complaints” as novel. |
| RBI distinguishes debit/no-beneficiary-credit and debit/no-merchant-confirmation; current documented outer TATs include T+1 and T+5 respectively, with stated compensation conditions. | [RBI TAT framework](https://www.rbi.org.in/commonman/English/scripts/Notification.aspx?Id=3074) | Model payment ambiguity states and safe wait/reconcile rules; never promise exact timing/reversal. |
| PhonePe says wrong successful UPI transfer cannot be simply reversed; recipient consent is required. | [PhonePe guidance](https://www.phonepe.com/blog/trust-and-safety/how-to-reverse-upi-payments-when-money-is-wrongly-transferred-or-is-in-pending-status/) | Wrong-recipient is information/evidence guidance only; never present as recoverable by product. |
| Google Pay tells customers not to retry a processing merchant payment, differentiates successful/processing/failed states, and directs cases to merchant/bank/NPCI routes. | [Google Pay merchant help](https://support.google.com/pay/india/answer/9494510?hl=en) | Product insight: merchant must know whether it is safe to ask customer to retry. |
| Razorpay customer refunds/disputes are merchant-led; Razorpay cannot refund on business behalf. Duplicate transaction customer guidance directs customer to seller. | [Razorpay customer refunds](https://razorpay.com/docs/payments/customers/customer-refunds/) | v0 opens duplicate review; it does not execute refund. |
| Razorpay Payment Links support Test Mode, callback verification, and webhook events. | [Payment Links APIs](https://razorpay.com/docs/payments/payment-links/apis/), [Webhooks](https://razorpay.com/docs/webhooks/payment-links/) | Use one bounded Test Mode recovery-link action after verified failure only. |
| Current Test Mode link creation is limited to 30 links per business. | [Create/Test Payment Links](https://razorpay.com/docs/payments/payment-links/create/) | Use fake provider in test/CI; manual Test Mode links only for proof. |
| Consumer reports show this is not theoretical: user account debited, merchant/recipient unpaid, user pays again, app/bank defer resolution. | [r/UPI report](https://www.reddit.com/r/UPI/comments/1u8116s/money_deducted_from_account_but_not_credited_to/) | Use as anecdotal user signal only; do not imply population statistics. |

## 2. Competitor conclusion

There are already consumer complaint routes, gateway payment APIs, finance reconciliation tools, **and a crowded Track 03 field of failed-payment retry agents**. Razorpay UPI Reserve Pay is a related *prevention* product (block funds first), not an ambiguity classifier. Stripe Smart Retries / Autopay Intelligent Retry recover *after* confirmed failure.

> The defensible v0 is a merchant-side front-office state machine: it blocks a harmful retry while the original payment is unresolved, restores captured-but-unlinked orders, and produces a bounded action or evidence packet.

See `COMPETITOR_STUDY.md` and `HACKATHON_AND_STACK_RESEARCH.md`.

**30/08/2026 field scan:** 10+ public Track 03 GitHubs (`reflex`, `RecoverAI`, `project-lazarus`, `due-revenue-recovery`, `Revora`, Navya Kaggle agent, plus `razorrecover` / `payrecover` name collision) all implement failed → diagnose → Payment Link / SMS. Differentiation is **unsafe retry rate = 0** and **captured-unlinked GMV**, not another Cohere/ADK retry bot.

**30/08/2026 stack decision:** do not adopt Google ADK, LangGraph, or Antom payment MCP as the product. Optional ADK leaf extractor only after the policy engine exists. Winners in 2026 agent hackathons were scored on fences, tests, holdout eval, HITL, and honest metrics — not framework logos.

## 3. Architecture decisions

| Date | Decision | Owner | Rationale | Rejected alternative | Revisit trigger |
|---|---|---|---|---|---|
| 30/08/2026 | Select Track 03 — AI Revenue Recovery. | Bhavesh | Direct match to payment degradation → root cause → bounded recovery. | Track 02 duplicate-fraud-only framing; Track 05 generic consumer complaint app. | If official rules prohibit simulated merchant recovery demo. |
| 30/08/2026 | Build merchant-side, not consumer complaint portal. | Bhavesh | Merchant controls order/retry/payment-link decision; apps/NPCI already own consumer grievance path. | NPCI-style Q&A/chatbot. | If a verified merchant partner/API requires consumer flow. |
| 30/08/2026 | Use synthetic payment incidents only. | Bhavesh | Privacy, permissions, regulation, public GitHub safety. | Real screenshots/statements/UTRs. | Never without written consent, legal review, and secure data design. |
| 30/08/2026 | Use deterministic state engine for final decision. | Bhavesh | Payment action cannot rest on LLM judgment. | LLM decides `failed`/`captured`. | Never relax without a strict evaluation and human review plan. |
| 30/08/2026 | Use Gemini only for optional structured extraction. | Bhavesh | Meaningful AI use without giving AI financial authority. | Fine-tuning / free-form agent. | If extraction adds no measurable value, remove it. |
| 30/08/2026 | Use Razorpay Test Mode Payment Link after verified `FAILED` only. | Bhavesh | Direct Buildathon relevance and clear recovery action. | Live mode, automatic refund. | If Test Mode access blocks, use fake provider and disclose. |
| 30/08/2026 | SQLite first, Postgres only for deployed staging. | Bhavesh | Six-day solo deadline; transactional schema is simple. | Supabase/Postgres day one, microservices. | If staging multi-user demo needs it. |

## 4. Assumptions to verify

| Assumption | Default | Why it matters | Action |
|---|---|---|---|
| Razorpay Test Mode account | Create fresh test keys by Slice 4 | Needed for real Test Mode proof | Bhavesh creates test keys locally; never shares secret in chat. |
| Gemini API access | Optional, free/available | Helps screenshot/text intake but not core flow | Build fake extractor first. |
| Public staging / tunnel | Optional | Required only for live webhook delivery proof | Decide after deterministic state machine works. |
| Merchant persona | Synthetic FitCart India | Keeps data safe; supports clear demo | Do not use real merchant records. |
| Deadline | 05/09/2026 | Only six days remain on research date | Freeze feature scope daily. |

## 5. Learning loop

After every slice, add a dated note:

```text
Slice / commit:
What worked:
What failed:
Evidence / commands:
Metric:
Scope change:
Next smallest task:
```

The Google Sheet Change Log records daily execution; this document records durable product/architecture decisions.
