# Hackathon Win Patterns & Stand-out Stack — PayState Bridge

**Research date:** 30/08/2026. Use this when choosing libraries and when writing the 5-minute pitch. Companion to `COMPETITOR_STUDY.md` and `TECH_STACK.md`.

## 1. This contest has no winners yet

[Razorpay AI Buildathon](https://razorpay.com/buildathon/) is a **hiring filter**, not a scored prize hackathon with a published winner list.

What they will look at:

| Artifact | Why it matters |
|---|---|
| Public GitHub repo | Proof of work. |
| Architecture | Can you explain money flow and failure. |
| ≤5-minute pitch video | One hard case, not a feature tour. |
| Track 03 bar | Detect → diagnose → **bounded** recovery; measured ₹; stopping rules; audit. |

There is no trophy to reverse-engineer. There *is* a crowded student field cloning “failed payment → new Payment Link”. Winning the *internship slot* means looking like a Razorpay AI Builder: judgment, safety, measured loop — not more agents.

## 2. Parameters 2026 agent-hackathon winners actually shipped

Synthesised from Microsoft Agent Academy, GitLab AI Hackathon, Neo4j video-agent hack, HackAgents BIU, Solo.io MCP, and Devpost payment/recon entries (full table in `COMPETITOR_STUDY.md`).

| # | Parameter | What winners did | What losers / clones did | PayState v0 mapping |
|---|---|---|---|---|
| 1 | Narrow painful loop | One workflow, end to end. | “Autonomous finance platform.” | Ambiguous payment → classify → one safe action. |
| 2 | Deterministic fence | LLM cannot fire irreversible tools. | LLM creates payment links / refunds. | Policy engine owns `DO_NOT_RETRY` / link / refund-review. |
| 3 | Structured I/O | Pydantic / JSON schema / Dataverse rules. | Free-form chat. | Pydantic case + action contracts. |
| 4 | Hidden / held-out eval | HonestLedger holdout vs reward hacking; Due 50 random worlds; Reflex pre-registered gates. | Demo of 3 happy rows. | Held-out synthetic set; unsafe retry = 0 is a hard gate. |
| 5 | Baseline comparison | Due: do-nothing / T+3 / blind retry / gated agent. | “We recovered ₹X” with no baseline. | vs “ask customer to pay again.” |
| 6 | Stopping rules | Max attempts, HITL, hard-stop phase. | Retry until recovered. | No second link while pending/unknown; one link after verified fail. |
| 7 | Audit / replay | Hash chain, correlation IDs, JSONL. | Screenshot of dashboard. | Append-only case timeline. |
| 8 | Tests in the repo | LORE: 43 tests; LedgerLine engine tests. | README-only. | Pytest policy + Playwright UI. |
| 9 | Honest limitations | Reflex published missed +15pp gate; Navya labelled assumed uplift. | Inflated GMV. | Label synthetic / Test Mode / no bank visibility. |
| 10 | Judge-mode demo | LedgerSoul locked browser flows; Lazarus `/chat` + `/dashboard`. | Localhost only, no script. | One-click synthetic incident → `DO_NOT_RETRY` → captured-unlinked attach. |
| 11 | Tool allow-list | Voodo deny-by-default; MCP.STORE protocol auth. | Unrestricted tool-calling. | Only: classify fields, wait, attach, one Test Mode link, open review, evidence packet. |
| 12 | Official starter used *well* | Neo4j winners extended typed schema. | Ignore vendor APIs or wrap them in 8 agents. | Razorpay Test Mode Payment Links + HMAC webhooks. Optional thin ADK for extraction only. |

**Do not add:** multi-agent swarms, vector DB, fine-tunes, Kubernetes, blockchain ledgers, “Hinglish voice” — those are already occupied Track 03 theatre.

## 3. Google ADK and other ready-made code — use / avoid

### 3.1 Google Agent Development Kit

- Docs: [google.github.io/adk-docs](https://google.github.io/adk-docs/)
- Code: [github.com/google/adk-python](https://github.com/google/adk-python) (`pip install google-adk`, Python 3.10+)
- Samples: [github.com/google/adk-samples](https://github.com/google/adk-samples) (~10k stars)

What ADK 2.0 actually gives that is useful:

| ADK feature | Useful for PayState? | How |
|---|---|---|
| `Agent` + tools | Yes, **extraction / draft reply only** | Wrap Gemini structured extract of synthetic SMS/screenshot. |
| `Workflow` graphs, HITL nodes, retries | Maybe later | Only if it does not own money tools. 6-day risk: extra framework. |
| `adk eval` + live eval extras (Aug 2026 Google blog) | Attractive on paper | Our eval is **policy correctness**, not voice-agent scoring. Prefer pytest fixtures. |
| ADK Web debugger | Nice | Optional; do not block Slice 0 on it. |
| Samples: `invoice-processing`, `llm-auditor`, `safety-plugins`, `agent-observability-bq` | Patterns, not dependencies | Read; do not vendor the whole sample. |
| Sample: **antom-payment** | **Anti-pattern for us** | LLM talks to Antom MCP to `create_payment_session` / refund. That is exactly the authority we forbid. |

**Decision (30/08/2026):** Do **not** make PayState “an ADK app”. Judges have seen ADK wrappers. If ADK is used, it is a **leaf extractor** behind FastAPI, with money tools unreachable from the agent.

Revisit only if: extractor quality is the demo bottleneck *and* ADK eval is free time after B2.

### 3.2 Allowed third-party libraries (Python / TS)

Keep the stack small. Every extra library must earn a safety or eval point.

| Library | Role | Stand-out value | Use in v0? |
|---|---|---|---|
| FastAPI + Pydantic v2 | API + contracts | Already planned; winners used typed schemas. | **Yes — core** |
| `google-genai` or official Gemini SDK | Structured output | Meaningful AI without ADK lock-in. | **Yes — extractor only** |
| Razorpay official Python SDK | Test Mode orders/links | Required proof. | **Yes — Slice 4** |
| Pytest + hypothesis (optional) | Policy tests | LORE-style test count. | **Yes pytest; skip hypothesis unless time** |
| Playwright | Merchant UI | Demo reliability. | **Yes — Slice 5** |
| `google-adk` | Optional extractor/workflow | Looks current; easy to overuse. | **No for Slice 0–3.** Optional leaf later. |
| LangGraph / LangChain / CrewAI | Multi-agent | Crowded; money-unsafe defaults. | **No** |
| LlamaIndex / Chroma / Qdrant | RAG | Wrong data shape (exact payment rows). | **No** |
| instructor / pydantic-ai | Stricter structured I/O | Fine if Gemini native structured output is flaky. | **Fallback only** |
| OpenTelemetry / Langfuse | Traces | GitLab/Solo winners used observability. | **Optional** after audit log works; do not block. |
| Stripe libraries | Smart Retries patterns | Wrong rail. | **No** |
| Antom / x402 / AP2 / A2A settlement kits | Agent payments | Track 01 / IntentBound leftover. | **No** |
| PhonePe / GPay / NPCI unofficial clients | “Real UPI” | Unavailable, unsafe, disqualifying. | **Never** |

### 3.3 Ready-made GitHub we may *read*, not fork as the product

| Repo | Take | Leave |
|---|---|---|
| `google/adk-samples` `safety-plugins`, `llm-auditor` | Callbacks that reject bad tool calls | Payment MCP that charges |
| Track 03 `project-lazarus` README | “LLM negotiator inside a fence” wording | Discount negotiation product |
| Track 03 `due-revenue-recovery` | Net value vs blind retry; publish the world where you lose | Retry control plane |
| Devpost LedgerLine | Engine tests before agents | Four-agent swarm |
| HonestLedger | Holdout against metric gaming | Self-improving rule rewriter (out of time) |

Do not copy their code into our repo. Copy the **discipline**.

## 4. What will make *this* project stand out in 6 days

Priority order — stop when the day is gone.

1. **Category break:** pending / captured-unlinked / duplicate, not “failed → link”.
2. **Unsafe retry rate = 0** on a held-out batch, shown in README and CI.
3. **One live Test Mode proof:** verified `FAILED` then exactly one payment link; pending case refuses the same API.
4. **Attach captured-but-unlinked** payment to order (this is real recovered GMV, not a retry).
5. **Honest README** modelled on Reflex/Due/Navya.
6. **Judge script:** 90 seconds pending (block), 90 seconds captured-unlinked (recover), 90 seconds failed (one link), 60 seconds architecture/safety.
7. Optional polish only: ADK extractor, OTel traces, pretty dashboard.

If we add Google ADK + LangGraph + Hinglish voice + Kubernetes, we become the median Track 03 clone with more logos.

## 5. Pitch one-liners grounded in this research

- “Reserve Pay stops some failures by blocking funds first. We stop a worse failure: charging the customer again while the first UPI state is still unknown.”
- “PhonePe already tells merchants not to accept a second payment when the dashboard says pending. We turned that sentence into a tested state machine.”
- “Most Track 03 repos recover after failure. We are graded on never creating the failure called ‘duplicate debit’.”
