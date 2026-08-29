# Five-Minute Demo Script — PayState Bridge

**Track 03 — AI Revenue Recovery · Razorpay AI Buildathon 2026**

---

## Before you start (setup checklist)

- [ ] API running: `uvicorn app.main:app --reload --port 8000`
- [ ] Web running: `npm run dev` (in apps/web)
- [ ] DB seeded: `python -m app.db.seed`
- [ ] Browser open: http://localhost:3000/cases
- [ ] Evaluation passed: `python -m app.evals.runner --split dev`

---

## Demo flow (5 minutes)

### 0:00 — Problem statement (30 seconds)

> "A customer pays with PhonePe. Their account shows 999 debited. The merchant has no confirmed order. Most merchant systems say: 'please pay again.' That creates a duplicate charge, a refund chase, and lost customer trust."

> "PayState Bridge stops that. It determines the safest next action from authoritative merchant/gateway evidence — before any recovery link is created."

---

### 0:30 — Scene 1: PENDING — do not retry (1 minute)

Open the cases list, find a PENDING case (INC-0001 or similar).

> "This customer says money was debited. But look at the gateway evidence: status is `PENDING`. The outcome is not known yet."

> "The system says: **DO NOT RETRY**. The recovery link button is disabled. The customer message says: 'Please do not pay again while we verify.'"

> "Same inputs always produce the same decision. No LLM decides payment state — only deterministic rules from gateway evidence."

---

### 1:30 — Scene 2: CAPTURED_UNLINKED — recover revenue (1 minute)

Find a CAPTURED_UNLINKED case.

> "This case is different. The gateway captured the payment — money was received. But the merchant's webhook failed, so the order stayed unpaid."

> "PayState Bridge matches the captured payment to the order by exact amount and reference. It marks the order `PAID_RECONCILED` — without asking the customer to pay again."

> "This is simulated recovered GMV. The audit trail shows exactly which evidence was matched and why."

---

### 2:30 — Scene 3: FAILED — verified recovery (45 seconds)

Find a FAILED case.

> "Now the gateway says: final failure. The payment never succeeded."

> "The system issues a recovery permit, then creates one Razorpay Test Mode link — labelled clearly as Test Mode. A second click returns the same link. The idempotency key prevents duplicate links."

---

### 3:15 — Scene 4: AI evidence intake (45 seconds)

In the case detail, scroll to the AI Evidence Intake panel.

> "The customer pastes a message: 'My PhonePe shows 999 deducted.' Our Gemini extractor reads the text and pulls out the amount, reported status, and UTR reference."

> "But notice — this output is labelled: **untrusted customer evidence**. The payment state comes from the gateway event, not the customer's message. AI extracts; deterministic rules decide."

---

### 4:00 — Scene 5: Evaluation metrics (45 seconds)

Show terminal output of eval runner.

> "We ran 60 synthetic test cases — 36 development, 24 held-out."

> "State accuracy is [X]%. The critical metric: **unsafe retry-link rate = 0%**. No PENDING or OUTCOME_UNKNOWN case ever got a recovery link. The CI fails if this number is ever non-zero."

> "Simulated GMV recovered: [X] — from captured-unlinked reconciliations. This is synthetic and clearly labelled."

---

### 4:45 — Close (15 seconds)

> "PayState Bridge proves that with deterministic policy, bounded AI extraction, and Test Mode payment links, a merchant can resolve payment ambiguity safely — before asking anyone to pay again."

---

## Panel Q&A prep

**Q: Why not just use an LLM for the whole thing?**
> Money decisions need deterministic, auditable results. The same inputs must always produce the same action. An LLM deciding payment state is a safety risk — we use Gemini only to extract structured fields from unstructured text.

**Q: What's the difference between this and NPCI UPI Help?**
> NPCI UPI Help is a consumer-facing grievance tool. PayState Bridge is merchant-side — it helps the merchant decide what to do before creating a second payment request. They operate at different layers.

**Q: Can you access real PhonePe/bank data?**
> No — and we're explicit about that. Gateway data is from Razorpay Test Mode or synthetic fixtures. The product's value is in the merchant-side decision logic, not bank-core access.

**Q: What happens if the AI extraction fails?**
> It falls back to `OUTCOME_UNKNOWN` with a human review recommendation. The deterministic engine never waits for AI output to make a safety decision.

**Q: Is the GMV figure real?**
> No — it's simulated from synthetic incidents. Every place we display GMV, it says "SIMULATED — synthetic data only." The eval report does the same.
