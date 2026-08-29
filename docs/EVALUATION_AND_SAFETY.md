# Evaluation, Safety & Operations — PayState Bridge

## 1. Evaluation principle

PayState Bridge is evaluated on a safety-first question:

> **When the first payment is unresolved, does the merchant avoid asking the customer to pay again?**

A high conversion rate with unsafe duplicate retries is failure. A safe escalation is better than a confident wrong recovery action.

## 2. Dataset design

Use **only synthetic incidents**. No real bank statement, customer screenshot, UTR, UPI ID, PhonePe/Google Pay export, or payment credential belongs in fixtures or prompts.

### Dataset split

| Split | Cases | Purpose |
|---|---:|---|
| Development | 36 | Implement and debug state rules/extraction. |
| Held-out | 24 | Run once for final reported metrics; do not tune against it. |
| Total | 60 | Enough for a solo Buildathon prototype; disclose limited sample size. |

### Required case balance

| State / failure type | Suggested total |
|---|---:|
| `PENDING` | 12 |
| `FAILED` | 10 |
| `CAPTURED_UNLINKED` | 10 |
| `DUPLICATE_SUCCESS` | 8 |
| `OUTCOME_UNKNOWN` / conflicting evidence | 8 |
| `WRONG_RECIPIENT` | 5 |
| `UNAUTHORIZED` | 3 |
| malformed / injection / extractor failure | 4 |

Each case has: synthetic order data, synthetic gateway events, optional customer report, expected state, expected action, simulated GMV, and reason code.

## 3. Required metrics

| Metric | Formula / meaning | Target / interpretation |
|---|---|---|
| State classification accuracy | correct final state / all held-out cases | Report honestly; not enough alone. |
| Unsafe retry-link rate | recovery links created for `PENDING` or `OUTCOME_UNKNOWN` / those cases | **0 is mandatory.** |
| Captured-unlinked recovery recall | correctly reconciled captured-unlinked cases / all such held-out cases | Primary revenue-recovery metric. |
| Duplicate-success detection recall | duplicate cases opened for review / known duplicate-success cases | Shows customer-protection value. |
| Verified recovery-link precision | recovery links on truly failed cases / all recovery links | Every link should be justified. |
| Simulated GMV recovered | sum of order value recovered by reconciliation + verified Test Mode recovery completion | Must be labelled synthetic. |
| Evidence-packet completeness | cases with required refs/timestamps/route / cases requiring escalation | Shows operational usefulness. |
| Customer-message safety | messages with no unsupported promise / all generated messages | 100% in fixture suite. |
| Extraction field accuracy | correct amount/status/ref fields from synthetic text/image | Optional; never substitute for state accuracy. |

### False-positive cost

A conservative recovery system may make operators review too many cases. Report this too:

```text
false-positive review cost
= valid cases unnecessarily escalated
× assumed review minutes
× stated support cost/minute
```

Example scenario assumption only:

```text
2 minutes per case × ₹300/hour = ₹10 per unnecessary escalation
```

Never present this as observed merchant cost.

## 4. Golden safety assertions

The evaluation command and CI must fail if any assertion fails:

```text
1. No RecoveryAction exists for PENDING or OUTCOME_UNKNOWN state.
2. Recovery permit exists only after final FAILED gateway evidence.
3. Customer report/screenshot cannot override gateway captured/failed evidence.
4. Captured payment can reconcile an order only if deterministic match policy passes.
5. Duplicate success creates review—not automatic refund.
6. Wrong-recipient case never promises reversal/recovery.
7. Unauthorized case never creates normal recovery link.
8. Invalid model/schema/image extraction becomes OUTCOME_UNKNOWN, not a recovery action.
9. Invalid Razorpay callback/webhook signature changes no case/order state.
10. Duplicate webhook event ID produces no second state transition.
11. Demo environment refuses live Razorpay key configuration.
12. Every customer-facing message says “do not pay again” for pending/unknown cases.
```

## 5. Evaluation runner shape

```text
for case in heldout_cases:
  create isolated synthetic DB state
  load merchant order + gateway events + customer report
  run optional fake extractor / provider adapter
  run deterministic classifier and recovery policy
  assert expected state and action
  if action is reconcile: assert order link policy
  if action is recovery link: use fake provider and assert original state FAILED
  write result and metric counters
write report.json + EVAL_REPORT.md
exit non-zero on golden safety failure
```

The final report must include:

- date and git commit;
- fixture split count;
- metrics table;
- passed/failed cases;
- known limitations;
- explicit statement: “All data and GMV figures are synthetic.”

## 6. Threat model

| Threat | v0 mitigation |
|---|---|
| Customer uses screenshot to claim success | Label screenshot/customer report as untrusted; wait for merchant/gateway evidence. |
| LLM invents UTR/status | Pydantic validates structure; deterministic engine cannot use model claim as final proof. |
| Support operator asks customer to retry | UI hides/disables recovery action for pending/unknown; safe response generated. |
| Duplicate payment from second link | Require permit + idempotency key; prohibit link generation while original outcome unresolved. |
| Webhook replay/forgery | Raw-body HMAC validation; event-ID receipt table; legal transition check. |
| Wrong recipient alleged | Provide official route guidance only; no recovery promise. |
| Secret leakage | Fresh Test Mode keys, env vars, scans; no secrets in screenshots/fixtures/CI caches. |
| Real data upload | Demo UI shows synthetic-only warning; file ingestion validates synthetic fixture flag in v0. |

## 7. Privacy and compliance boundary

- This prototype is not a bank, PA, PSP, NPCI participant, grievance authority, or regulated complaint-filing service.
- It must not request or display UPI PIN, OTP, CVV, full bank account number, real UPI ID, or real statement.
- A real future product would require merchant agreements, data-protection design, authentication, audit retention policy, and legal/regulatory review. None are claims of v0.
- Customer text is redacted in logs; public demo uses generated text only.

## 8. Quality and operations baseline

| Area | Minimum baseline |
|---|---|
| Validation | Strict Pydantic schemas; money in paise; enums for all states/actions. |
| Authorization | No public operator actions in staging without a demo-admin guard. |
| Testing | ≥25 unit tests, ≥8 API integration tests, ≥4 Playwright flows, 24 held-out cases. |
| Observability | Correlation ID, case ID, source type, policy version, state/action, latency, provider outcome. |
| Health | `/health` without secrets; report dependency availability. |
| Data | Versioned fixture generator; migrations if DB schema changes. |
| Cost | One bounded extraction call + one bounded retry; input/image size limit; fake provider in CI. |
| Deployment | Separate local/staging config; no Live Mode. |
| Recovery | Fake provider provides fallback when Razorpay Test Mode unavailable. |

## 9. Release gate

A human must approve release/submission after confirming:

- [ ] all data and screenshots are synthetic;
- [ ] no live credential or payment action is configured;
- [ ] held-out evaluation executed and report saved;
- [ ] unsafe retry-link rate is zero;
- [ ] all golden safety assertions pass;
- [ ] Test Mode webhook/callback proof is either verified or limitation is prominently disclosed;
- [ ] no claim of bank/NPCI/app access, recovery guarantee, or automatic complaint filing;
- [ ] mobile console works at 360px and error/empty/loading states are visible;
- [ ] repository secrets scan and CI are green;
- [ ] rollback is possible by disabling recovery-link endpoint and returning to final tagged commit.
