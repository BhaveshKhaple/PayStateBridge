# Experience & Simulator Design — PayState World

**Written:** 30/08/2026, after reviewing the live repo ([BhaveshKhaple/PayStateBridge](https://github.com/BhaveshKhaple/PayStateBridge)). Companion to `PRD.md`, `BUILD_PLAN.md`, `COMPETITOR_STUDY.md`.

## 0. The honest problem with the current build

The current app is a homepage, a merchant console listing synthetic cases, and API docs. Technically fine. **Emotionally dead.**

A Razorpay reviewer opens it and sees rows in a table. They never *feel* the bug we exist to kill: the 40 seconds where a customer has been debited, the merchant sees nothing, and everyone is about to make the expensive mistake of paying twice.

> Knowledge you can't show doesn't exist. The evaluation happens in a 5-minute video and a public repo — the *experience* is the product.

Every other Track 03 submission demos **their agent**. We will demo **the world failing** — and our agent holding the line inside it. That is the thing nobody else will build, because everyone else is busy wiring Cohere to a payment link.

## 1. The concept: PayState World — one screen, three truths

The core of the real-world bug is that **three parties see three different truths at the same moment.** No API doc shows this. So we build a miniature UPI universe where the judge can watch all three at once:

```text
┌─────────────────────┬──────────────────────┬─────────────────────┐
│  CUSTOMER'S TRUTH   │     THE RAILS        │  MERCHANT'S TRUTH   │
│  (fake UPI phone)   │  (god view)          │  (console + agent)  │
│                     │                      │                     │
│  ₹499 · Processing… │  Bank → Switch → PSP │  Order #1241 UNPAID │
│  SMS: ₹499 DEBITED  │  → Merchant          │  [Pay again] button │
│  [ Pay again ]      │  packet STUCK at     │  is GATED by agent  │
│                     │  Switch, T+38s       │  🔒 BLOCKED         │
└─────────────────────┴──────────────────────┴─────────────────────┘
```

- **Left — Customer's truth.** A believable phone-frame UPI app (synthetic, "PhonePe-style" but clearly fake-branded). Pay ₹499 → spinner → "Processing…" → SMS banner: `BH-HDFCBK: ₹499.00 debited`. A big amber **Pay again** button begs to be pressed.
- **Middle — The Rails (god view).** The synthetic network no human ever gets to see: Customer Bank → UPI Switch → Razorpay → Merchant, with the payment packet visibly moving, stalling, or getting lost. Under it, the **Chaos Panel**.
- **Right — Merchant's truth.** The existing console, upgraded: order unpaid, an **"Ask customer to pay again"** action — visibly **gated by the agent**. Try to fire it while the packet is stuck: red gate slam, `BLOCKED — payment still PENDING. A retry now risks a duplicate debit. Evidence: …`

Then the delayed webhook finally lands in the Rails view. The packet arrives. State flips to `CAPTURED_UNLINKED` → the agent **links it to order #1241**. Green tick across all three panes. Metrics ribbon updates: **₹499 recovered · 0 unsafe retries · 0 duplicate debits.**

The judge just watched the bug happen, watched the industry-standard instinct (retry) get physically blocked, and watched revenue get recovered *without a second charge*. That is the demo.

## 2. The Chaos Panel — the judge breaks the world

This is what makes it a simulator, not a video. Buttons and sliders that inject failure into the rails:

| Control | Effect | What the agent must do |
|---|---|---|
| `webhook delay` slider (0–120s) | Capture event arrives late | Hold `PENDING`, refuse retry the whole time |
| **Lose the webhook** | Payment captured, merchant never told | Later reconciliation → `CAPTURED_UNLINKED` → attach → recover GMV |
| **Customer mashes Pay again** | Second attempt from the phone pane | Detect `DUPLICATE_SUCCESS` risk → open human refund review, never silently refund |
| **Bank timeout** | Switch never responds | `OUTCOME_UNKNOWN` → evidence packet (UTR, order id, timestamps), safe customer reply |
| **Double-click race** | Two identical checkout requests | Idempotency proof: one order, one case |

The judge is not watching us pass our own test. **They are trying to break the safety law live, and failing.** That is a GitLab-judge-style "feels like a product" moment.

## 3. Timeline scrubber — because this bug is made of *time*

The entire problem is that the merchant decides at T+5s and the truth arrives at T+40s. So the world gets a **time scrubber**: replay the event stream, drag back to the ambiguity window, watch each pane's truth diverge and re-converge. Under the hood this is free — the event log is the state.

## 4. Judge Mode — three scripted stories

One-click scenarios on the landing view, each a real documented pain pattern (from our competitor research — synthetic re-enactments, no real data):

1. **"The Cab Driver"** — your lived story. Pending debit, driver unpaid, second payment elsewhere → `DUPLICATE_SUCCESS` → merchant-approved refund review. Ends with: *"This is the 45-minute support nightmare, compressed into 60 seconds."*
2. **"The ₹43,994 Miss"** — captured but webhook lost. Agent reconciles at close → attaches payment to order → GMV recovered without touching the customer.
3. **"The Portal Timeout"** — UTR exists, merchant page still spinning → `OUTCOME_UNKNOWN` → evidence packet + "do not pay again" customer message.

Each story runs ~60–90 seconds. The pitch video records these; the live URL lets the judge replay them.

## 5. Visual language — make it feel like a war room, not a CRUD app

- Dark theme, subtle grid, monospace evidence labels.
- **Color = state, globally consistent:** amber = PENDING (danger of wrong action), red = unsafe/blocked, green = recovered, grey = unknown.
- Motion is information: the packet's movement *is* the payment's truth. Keep it CSS/SVG — no animation library needed, maybe `framer-motion` only if it stays smooth.
- Big numbers ribbon on top: `₹ recovered without a second charge` · `unsafe retries blocked` · `duplicate debits prevented` · `policy violations: 0`.
- Every agent decision renders its **evidence chain** inline (event ids, timestamps, rule fired) — the audit trail is visible, not a log file.

## 6. Technical design (fits the existing repo, no stack change)

```text
apps/api
  app/sim/
    engine.py        # deterministic event scheduler: fixtures → events at T+x
    fixtures/*.json  # the 3 Judge Mode stories + chaos injections
    stream.py        # SSE endpoint /sim/stream — world ticks + events
  (policy engine, cases, classifier: unchanged — the sim feeds IT, not the other way)

apps/web
  app/world/page.tsx       # the three-pane universe
  components/PhonePane.tsx # fake UPI app (state machine driven by SSE)
  components/RailsPane.tsx # SVG nodes + moving packet + chaos controls
  components/ConsolePane.tsx
  components/TruthBar.tsx  # verdict banner: what the agent decided and why
```

Key properties:

- **The simulator does not fake the agent.** The sim emits the same event shapes a real PSP would; the existing classifier/policy engine consumes them. The gate that slams in the UI is the real policy decision. That is the integrity that survives a panel grilling.
- **SSE, not WebSocket.** One direction, simple, deploys anywhere.
- **Deterministic seeds.** Every story replays identically — same property that made Reflex/Due credible.
- **Deploy:** web → Vercel, api → Railway (Reflex proved this combo works for exactly this stack). The submission links a **live URL** — most students ship localhost screen recordings.

## 7. Re-plan: what changes in the 6 days

Keep: policy engine, classifier, Test Mode link slice, eval harness, README honesty.

**Cut / defer:** broad dashboard CRUD polish, extra cases beyond the 3 stories, ADK extractor, OTel, any multi-agent experiment. The World *is* the polish.

| Slice | Task | Proves |
|---|---|---|
| X-01 | Sim engine + SSE stream + one fixture | World ticks, console receives events |
| X-02 | Phone pane (pay → processing → debited → pay-again temptation) | Customer truth visible |
| X-03 | Rails pane + chaos panel | God view + judge can inject failures |
| X-04 | Console action gate + TruthBar + metrics ribbon | The BLOCKED moment lands |
| X-05 | 3 Judge Mode stories + timeline scrubber | The demo script |
| X-06 | Vercel/Railway deploy + record the 3 stories for the video | Live URL + submission assets |

## 8. How to say it

> "Everyone else built an agent that reacts to a failed payment. I built the world the payment gets stuck in — and an agent that provably refuses to make it worse. Here, try to break it."

> "Razorpay's own docs say don't retry while pending. I turned that sentence into a state machine you can watch holding the line — press the button yourself."
