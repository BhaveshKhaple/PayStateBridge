# Competitor & Alternative Study — PayState Bridge

**Research date:** 30/08/2026. Official docs and public repos are cited. Inference is labelled. This is the parallel study to the earlier IntentBound competitor work: alternatives first, then honest gap, then what we must not claim.

## 0. Category truth

PayState Bridge is **not** the first product in payments, disputes, retries, or revenue recovery.

The defensible category is narrower:

> **Merchant-side, front-of-house prevention of an unsafe customer retry when the first payment outcome is still ambiguous.**

Three other categories already exist and we must not pretend they do not:

1. **Consumer grievance rails** — NPCI UPI Help, PhonePe/GPay/bank disputes, RBI CMS.
2. **Gateway retry / dunning rails** — Razorpay Autopay Intelligent Retry, Stripe Smart Retries, WhatsApp recovery links.
3. **Back-office reconciliation / chargeback tools** — finance matching, Stripe Smart Disputes, Chargeflow.

PayState sits **before** a second charge is created, not after a confirmed failure and not after month-end close.

## 1. Official alternatives (India rails)

| Alternative | What it solves | Evidence | What it does not solve here |
|---|---|---|---|
| NPCI UPI Help | Consumer Q&A, status, grievance, mandates. | [upihelp.npci.org.in](https://upihelp.npci.org.in/) | Does not know a merchant order or whether a replacement link is safe. |
| PhonePe Help + UDIR | In-app pending/failed/wrong-payment reports; auto-resolution path. | [PhonePe reverse/pending](https://www.phonepe.com/blog/trust-and-safety/how-to-reverse-upi-payments-when-money-is-wrongly-transferred-or-is-in-pending-status/), [PhonePe merchant failed-UPI guide](https://business.phonepe.com/articles/upi-transaction-failed-but-money-deducted-complete-resolution-guide) | Does not operate inside merchant checkout to stop an unsafe retry. |
| Google Pay dispute flow | Status, troubleshooting, merchant/bank/NPCI routes. | [GPay merchant help](https://support.google.com/pay/india/answer/9494510?hl=en) | Tells the user whom to contact; does not map payment ↔ order. |
| RBI TAT / CMS | T+1 P2P and T+5 P2M outer reversal windows; Ombudsman. | [RBI TAT](https://www.rbi.org.in/commonman/English/scripts/Notification.aspx?Id=3074) | Regulatory after-the-fact path, not a checkout state machine. |
| Razorpay customer refunds | Customer tracks a refund **after** the business acts. | [Razorpay customer refunds](https://razorpay.com/docs/payments/customers/customer-refunds/) | Razorpay will not refund on the merchant’s behalf. |
| Razorpay Payment Links + webhooks | Create/test links; `paid` / `expired` / `cancelled`. | [Payment Link APIs](https://razorpay.com/docs/payments/payment-links/apis/), [webhooks](https://razorpay.com/docs/webhooks/payment-links/) | Rails only. Merchant still owns retry safety. |
| Idempotency keys | Stop identical technical retries. | Industry standard | Cannot stop a human paying again from another app while payment 1 is pending. |

**PhonePe’s own merchant guidance (Mar 2026) already states the core rule we productize:** wait before retry; if the dashboard shows pending, do not accept another attempt; duplicate authorisations create reconciliation nightmares. ([source](https://business.phonepe.com/articles/upi-transaction-failed-but-money-deducted-complete-resolution-guide))

That is advice in a blog. It is not a working merchant agent with a zero unsafe-retry eval gate.

## 2. Adjacent Razorpay products — including Reserve Pay

These are **related**, not clones. Reviewers will ask about them.

| Product | What it actually is | Relation to PayState | Do not do |
|---|---|---|---|
| [UPI Reserve Pay / SBMD](https://razorpay.com/docs/payments/recurring-payments/upi-reserve-pay/) | Customer blocks a spending limit once; merchant debits as value is delivered. Live product, category-gated, max block ₹10,000, token up to 90 days. | Prevents *some* checkout failures by pre-authorising. Does **not** classify a pending PhonePe debit vs unpaid merchant order, and does not stop a panicked second payment on a different VPA/app. | Do not rebuild Reserve Pay. We have no SBMD activation, and it is the wrong problem. Optional later: mention it as a *prevention* sibling, not v0 scope. |
| [UPI Autopay + Intelligent Revenue-Protect](https://razorpay.com/blog/upi-autopay-with-intelligent-revenue-protect/) | Mandate drop-off recovery, intelligent retry engine (FTX 2026), WhatsApp recovery links after failed debit. | Classic **confirmed-failure** dunning. Track 03 crowd is cloning this. | Do not become “smarter Autopay retry”. |
| [UPI error mapping / Turbo UPI / dynamic routing](https://razorpay.com/blog/tackling-upi-payment-failures-with-razorpay/) | Translate NPCI codes, route terminals, reduce mid-flow drop-offs. | Helps *known* failures. Ambiguous pending is a different state. | Do not claim we replace routing. |
| Razorpay Agent Studio / Agentic Payments | Hosted agent tools across payments. | Official product. Cloning it is disallowed by our own rules. | Use Test Mode APIs; do not clone Agent Studio agents. |

**Reserve Pay vs PayState in one line**

```text
Reserve Pay  = authorise once, debit later (prevents some failures)
PayState     = payment already happened / is pending; do not charge again until state is known
```

## 3. Global “revenue recovery” products (not India-UPI twins)

| Product | Pattern | Why it is not our v0 |
|---|---|---|
| [Stripe Smart Retries](https://docs.stripe.com/billing/revenue-recovery/smart-retries) | AI chooses when to re-attempt a **failed** invoice; hard declines need a new PM. | Confirmed failure + card/subscription world. No UPI pending/unlinked-order problem. |
| Stripe revenue recovery emails / card updater | Dunning after known failure. | Same. |
| Stripe Smart Disputes / Chargeflow / Chargeblast | Compile chargeback evidence. | Track 02 territory, after a dispute exists. |
| Chargeflow Alerts | Stop chargebacks before they file. | Fraud/dispute, not payment-state ambiguity. |

Use these only as **pattern references** (stopping rules, hard vs soft decline, measured recovery). Do not copy their category into the pitch.

## 4. Track 03 field — this Buildathon is already crowded

Razorpay AI Buildathon **has no winners yet**. Deadline is 05/09/2026. Selection is a hiring panel on public repo + ≤5-min video + architecture. ([official page](https://razorpay.com/buildathon/))

What *does* exist: a dense cluster of student Track 03 repos, almost all doing the **same loop**:

```text
payment failed → diagnose cause → retry / SMS / WhatsApp / new Payment Link
```

Public examples inspected 30/08/2026:

| Repo / post | What they built | Strong move | Weak / crowded move |
|---|---|---|---|
| [abhinav-phi/reflex](https://github.com/abhinav-phi/reflex) | Rules-first + LLM tail, EV-ranked interventions, hash-chained ledger, pre-registered eval vs naive retry, live Vercel/Railway demo. | Honest eval (missed +15pp gate, published anyway). | Failed-subscription recovery — official example direction. |
| [AdithyaAbburi/RecoverAI](https://github.com/AdithyaAbburi/RecoverAI) | Risk score → LLM diagnosis → Expected Recovery Value → policy gate. | Explicit 0% policy-violation metric. | Same failed-tx recovery category; local DeepSeek as theatre. |
| [ShaunT06/project-lazarus](https://github.com/ShaunT06/project-lazarus) | “LLM is a negotiator inside a fence”; HMAC webhooks; 50-case batch; live `/chat` + `/dashboard`. | Best articulation of fence vs LLM. | Checkout drop-off / discount negotiation — another listed example. |
| [n-3-0-l-d-3-v/due-revenue-recovery](https://github.com/n-3-0-l-d-3-v/due-revenue-recovery) | Policy-gated control plane; 0 violations vs 2,493 for blind retry; net value not raw recovery %. | The metric judges will love: **blind retry recovers more rupees and is worth less**. | Still retry-orchestration, not ambiguity. |
| [Param-Maheshwari/Revora](https://github.com/Param-Maheshwari/Revora-AI-Revenue-Recovery-Agent) | Hinglish messages, compliance gate, tone A/B. | Matches the “Hinglish voice recovery” example direction. | Messaging layer on failed payments. |
| [Navya2057/AI-Revenue-Recovery-agent](https://github.com/Navya2057/AI-Revenue-Recovery-agent) | Kaggle card declines, GBTs, bounded actions, honest limitations in README. | Honest “uplift is assumed, not learned”. | Card POS log, not Indian UPI/Razorpay Test Mode. |
| Ayush Tiwari LinkedIn (23/08/2026) | FastAPI + Cohere + Razorpay Payment Links + webhooks: fail → ML → link → RECOVERED. | Clean demo story. | **The default clone.** If we ship this, we are invisible. |
| Neeraj Mittal “Reclaim” LinkedIn | Cause-aware retry timing, stop rules, Docker/K8s/Grafana. | Stopping rules. | Involuntary churn Autopay clone. |
| 10+ other GitHub names (`razorrecover`, `recoverai`, `payrecover`, `CascadeGuard`, …) | Same nouns: failed payment, recovery agent, payment link. | — | Name collision is already real. |

**Implication:** “AI that sends a Razorpay recovery link after a failed payment” will not differentiate. Track 03’s own example list already names it.

**PayState’s wedge against this field**

```text
They recover AFTER failure is known.
We refuse to create payment two WHILE payment one is unknown.

Unsafe retry-link rate = 0 is the headline metric.
Captured-but-unlinked GMV is the recovery metric.
```

## 5. Hackathon-winner patterns (2026, adjacent contests)

These are **not** Razorpay winners. They are what independent 2026 agent-hackathon judges actually rewarded. Copy the *parameters*, not the products.

| Contest | Winner / standout | Why it won (judges said) | Parameter to steal |
|---|---|---|---|
| [Microsoft Agent Academy, Jun 2026](https://devblogs.microsoft.com/powerplatform/agent-academy-hackathon-winners/) | VendorGuard (highest score overall) | Email → extract → 4 specialist agents → 15 **rules** in Dataverse, RAG/red-amber-green, queryable report in <2 min. | Rulebook outside the LLM; event-triggered loop; audit. |
| Same | Vehicle insurance self-service (3rd, Recruit) | Live data decisions; **human escalation after 2 failed ID checks**; explicit confirm before irreversible action. | HITL before money/irreversible tools. |
| Same | Client Kick-off Skill | Two-phase workflow: read-only, **hard stop**, then per-item approval. | Hard stop between propose and execute. |
| Same | SprintForge | Transcript → structured JSON → MCP tools (Learn + Jira). | Structured output + real tools, not chat. |
| Judging weights | Accuracy 25%, execution 25%, UX 15%, originality 15%, **reliability & safety 10%**, impact 10%. | Safety is scored, not optional. | Ship eval + audit, not only demo. |
| [GitLab AI Hackathon 2026](https://about.gitlab.com/blog/gitlab-ai-hackathon-2026-meet-the-winners/) | LORE (Grand Prize) | “Feels like a product”; **43 tests** in a hackathon repo; router + loop prevention. | Tests, dashboard, anti-loop. |
| Same | DocSync | Detector / Writer / Reviewer; **if low confidence, file a human issue** instead of auto-PR. | Confidence-gated write. |
| Same | Time-Traveler | Safe copy of prod, then migrate. | Never mutate live money/state first. |
| [Hack the Video Agent, Aug 2026](https://collabnix.com/neo4j/2026/08/01/one-starter-repo-three-winners-neo4j-at-hack-the-video-agent-context-graph/) | MealPrep et al. | Used the **starter + Pydantic structured outputs**; schema expansion was cheap. | Typed schemas, don’t fight JSON. |
| [HackAgents BIU 2026](https://github.com/VooDo-AI/voodo-HackAgents-BIU-2026) | Voodo | Vision loop **plus** deny-by-default tools, session caps, panic button, audit redaction. | Tool allow-list and caps. |
| [Solo.io MCP hackathon](https://www.solo.io/blog/celebrating-the-winners-of-the-2026-hackathon-for-mcp-ai-agents) | Frugalia, MCP.STORE | Detect → analyse → resolve; protocol-level auth so agents **cannot bypass** security. | Money tools must be ungatable by the model. |
| Devpost payment/recon | [Reconly](https://devpost.com/software/agentic-ai-payment-reconciliation-platform), [LedgerLine](https://devpost.com/software/ledgerline), [HonestLedger](https://devpost.com/software/honestledger), [LedgerSoul](https://devpost.com/software/ledgersoul) | Deterministic matcher first; LLM only on remainder; **holdout against reward hacking**; “AI proposes, code verifies”; judge-mode demo. | Hybrid engine + hidden eval set. |

**Repeated winning formula (plain language)**

1. One painful, specific loop — not a platform.
2. Deterministic code owns money / irreversible tools.
3. LLM structures, drafts, or ranks *inside a fence*.
4. Batch metric + baseline + honest miss.
5. Audit trail a judge can replay.
6. Five-minute demo of the hard case, not the happy path.
7. Tests in CI.

Razorpay’s own Track 03 bar matches this exactly: measured money recovered, compliant escalation, **stopping rules**, audit trail. ([buildathon](https://razorpay.com/buildathon/))

## 6. Social proof of the *problem* (not of our solution)

These are anecdotes. Do not quote them as market size.

| Source | Signal |
|---|---|
| [r/UPI — PhonePe processing, paid twice](https://www.reddit.com/r/UPI/comments/1u8116s/money_deducted_from_account_but_not_credited_to/) | Debit + unpaid recipient + second payment + app/bank finger-pointing. Lived example we already use. |
| [r/UPI — BHIM pending 48h, banks bounce](https://www.reddit.com/r/UPI/comments/1vdkgqf/i_did_a_payment_on_31st_july_8pm_money_deducted/) | Pending + debited; BHIM says talk to HDFC. |
| [r/UPI — ₹43,994 debited, merchant unpaid](https://www.reddit.com/r/UPI/comments/1up0o0z/transaction_debited_but_merchant_has_not_received/) | High-value merchant miss. |
| [r/UPI — hotel first attempt unclear, paid again](https://www.reddit.com/r/UPI/comments/1vsrzc7/upi_payment_debited_but_receiver_hasnt_received/) | Exact “retry under ambiguity” failure. |
| [r/UPI — CRED/PayU/Income Tax, UTR exists, portal waiting](https://www.reddit.com/r/UPI/comments/1ukar5z/has_anyone_faced_a_situation_where_a_upi_payment/) | Captured-but-unlinked analogue. |
| [Quora — merchant denying receipt](https://www.quora.com/The-transaction-was-successful-but-the-merchant-denying-receiving-the-amount-What-are-the-options-that-I-have) | Generic “collect evidence, mail merchant+bank”. No product. |
| LinkedIn | Official Razorpay Careers posts (proof-of-work hiring). Student Track 03 posts are almost all failed-payment retry agents. Fiber keyword search is noisy; named posts above were found via web index. |
| X/Twitter search `Razorpay Buildathon Track 3` | No useful public thread on 30/08/2026. |
| YouTube | 2026 hackathon *promo* videos, not payment-recovery winner breakdowns. Do not cite as product evidence. |

## 7. Positioning

### Say

> “A merchant-side payment-ambiguity recovery agent. It resolves before retrying.”

> “It does not replace NPCI, PhonePe, GPay, banks, Reserve Pay, or Razorpay Autopay. It stops the merchant from asking the customer to pay again while payment one is still unknown.”

> “Track 03 is full of failed-payment retry agents. We measure **unsafe retry-link rate = 0** and recovered **captured-but-unlinked** GMV.”

### Do not say

- “India has no UPI complaint solution.”
- “We invented revenue recovery.”
- “We are like Reserve Pay / Stripe Smart Retries / Chargeflow.”
- “We recover money from PhonePe/GPay/banks.”
- “We file NPCI complaints / reverse wrong UPI / guarantee refund.”
- “Google ADK / multi-agent / blockchain makes this novel.”

## 8. Moat for a 6-day Buildathon

Not a startup moat. Execution moat:

1. State taxonomy that includes `PENDING` and `CAPTURED_UNLINKED`, not only `FAILED`.
2. Deterministic **no-retry** policy with tests.
3. One Razorpay Test Mode link, and only after verified failure.
4. Held-out eval: unsafe retry rate must be zero.
5. Honest README limitations (Reflex/Due/Navya already set that bar).
6. Evidence packet that points to official rails instead of faking them.

See `HACKATHON_AND_STACK_RESEARCH.md` for winner parameters and which libraries we actually use.
