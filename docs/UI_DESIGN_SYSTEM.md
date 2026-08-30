# UI Design System — PayState World

**Written:** 30/08/2026. Governs every pixel of the World experience (`EXPERIENCE_AND_SIMULATOR.md`). Load the `/premium-ui-craft` workflow before any UI slice; this file is its project-specific token + component contract. One theme only: **dark, done excellently** — we do not ship two themes adequately.

## 0. Design intent

> Open the page. First frame, before reading a word: **"this is a real payment-operations product."**

Three surfaces, one glance, three truths. Restraint is the aesthetic — charcoal, hairlines, one amber that means *danger of wrong action*, tabular money, zero decoration.

## 1. Tokens (write these as CSS variables first, in `apps/web/app/globals.css`)

```css
:root {
  /* Surfaces — charcoal steps, never pure black, elevation = lighter + hairline */
  --bg-0: #0a0a0b;            /* page canvas */
  --bg-1: #101013;            /* pane base */
  --bg-2: #16161a;            /* cards, elevated */
  --bg-3: #1d1d23;            /* hover, popovers */
  --hairline: rgba(255,255,255,0.07);
  --hairline-strong: rgba(255,255,255,0.12);

  /* Text */
  --ink:    #fafafa;          /* headlines, key numbers */
  --body:   rgba(250,250,250,0.72);
  --muted:  rgba(250,250,250,0.45);
  --faint:  rgba(250,250,250,0.28);

  /* ONE accent — indigo. Interactive affordance only. */
  --accent: #6e6df0;          /* Linear-family indigo */
  --accent-soft: rgba(110,109,240,0.14);

  /* Semantic — muted, never neon. These are MEANING, globally consistent. */
  --pending:  #e8a33d;        /* amber  = PENDING / ambiguity / danger of wrong action */
  --blocked:  #e5484d;        /* red    = unsafe action blocked, violation */
  --recovered:#46a758;        /* green  = recovered / resolved / verified */
  --unknown:  #8b8b93;        /* grey   = OUTCOME_UNKNOWN / not yet knowable */
  --pending-soft: rgba(232,163,61,0.12);
  --blocked-soft: rgba(229,72,77,0.12);
  --recovered-soft: rgba(70,167,88,0.12);

  /* Type */
  --font-sans: 'Inter Variable', 'Inter', -apple-system, sans-serif;
  --font-mono: 'Geist Mono', 'JetBrains Mono', ui-monospace, monospace;

  /* Radii */
  --r-sm: 6px;  --r-md: 8px;  --r-lg: 12px;  --r-phone: 36px;

  /* Motion */
  --m-fast: 120ms ease-out;
  --m-std: 240ms cubic-bezier(0.25,0.46,0.45,0.94);

  /* The only shadow — floating layers only */
  --shadow-float: 0 8px 32px rgba(0,0,0,0.35);
}
```

**Money and IDs are always mono + `font-variant-numeric: tabular-nums`.** Amounts like `₹499.00` never reflow width when digits change — this alone kills the "demo jank" look.

## 2. Type scale (5 sizes, that's all)

| Token | Size / lh / tracking / weight | Use |
|---|---|---|
| display | 28px / 1.15 / −0.02em / 600 | World headline, story titles |
| title | 17px / 1.3 / −0.012em / 590 | Pane titles, card heads |
| body | 14px / 1.6 / 0 / 400 | Everything readable |
| caption | 12px / 1.4 / 0 / 500 | Pane eyebrows: `CUSTOMER'S TRUTH` |
| mono-data | 12–13px / 1.5 / 0 / 400 | IDs, timestamps, amounts, evidence |

Pane eyebrows are uppercase mono with 0.08em tracking in `--muted`. Numbers in the metrics ribbon: 32px display weight in `--ink`, label in caption mono under it.

## 3. Layout — the World grid

```text
┌──────────────────────────────────────────────────────────────┐
│ TopBar  PayState Bridge · Track 03      [story picker] [⌘K?] │
├──────────────────────────────────────────────────────────────┤
│ Metrics ribbon: ₹ recovered · retries blocked · dup prevented│
│                 · policy violations 0        [time scrubber] │
├────────────────┬──────────────────────┬──────────────────────┤
│ CUSTOMER'S     │   THE RAILS          │  MERCHANT'S TRUTH    │
│ TRUTH          │   (god view)         │  (console + gate)    │
│ phone frame    │   packet diagram     │  order card + action │
│                │   chaos panel below  │  TruthBar + evidence │
├────────────────┴──────────────────────┴──────────────────────┤
│ Event timeline (mono, hairline rows, the audit trail)        │
└──────────────────────────────────────────────────────────────┘
```

- Viewport-fit on desktop (this is a demo instrument, not a scroll page): `100dvh`, panes `1fr 1.2fr 1fr`, 1px hairline dividers, no page scroll on the World view.
- Each pane = one role, one background step (`--bg-1`), padded 20–24px.
- Mobile: panes stack vertically, phone first — the demo is recorded on desktop; mobile just needs to be clean.

## 4. Component specs

### 4.1 PhonePane (customer's truth — must read as a REAL UPI app)
- Phone frame: `--r-phone` radius, 1px `--hairline-strong`, subtle inner bezel (`--bg-0`), status bar with mono time + battery glyph. Inside is **light** (UPI apps are light) — deliberate contrast island: `#ffffff` inner screen, dark text. This one inversion makes the phone pop out of the dark war room.
- Fake brand: "UPI Pay" wordmark, clearly synthetic; no real brand assets.
- States: idle pay sheet → **Processing…** (spinner + "Do not press back" — authentic UPI copy) → SMS banner slides down from top: `BH-HDFCBK • ₹499.00 debited • Ref 3124…` (mono ref) → amber **Pay again** button pulsing gently (border pulse, not glow).
- The pulse stops the instant the case resolves. Motion = information.

### 4.2 RailsPane (god view)
- Four nodes on one horizontal line: `Customer Bank → UPI Switch → Razorpay → Merchant`, drawn as bordered circles with mono labels. Packet = a small dot travelling the line, CSS-animated, driven by SSE timing (never fake timers).
- Stuck packet: pulses amber at the stuck edge; the affected edge's line goes `--pending` dashed.
- Chaos panel below: mono-labelled buttons (`lose webhook`, `retry storm`, `bank timeout`) as ghost buttons (hairline border, `--body` text), slider for webhook delay. When a chaos is armed, its button gets a `--pending-soft` fill.
- This pane is the "nobody ever shows you this" moment — keep it diagram-clean, no chrome.

### 4.3 ConsolePane (merchant's truth)
- Order card: `#1241 · ₹499.00 · UNPAID` (status pill = amber dot + word), customer row, items row — dense, hairline-separated.
- The gated action: full-width button `Ask customer to pay again`. Default state **armed but safe**: pressing while PENDING/UNKNOWN triggers the gate-slam — button flashes `--blocked`, shakes 120ms, and below it the verdict card expands:
  `🔒 BLOCKED · Payment still PENDING · Rule: never retry while unresolved · Evidence: evt_8841, evt_8842 (mono, 12px)`.
- When verified FAILED: the same button becomes enabled with `--accent`, label `Create one recovery link (Test Mode)`.
- TruthBar pinned at pane bottom: one sentence, mono prefix `verdict ›`, e.g. `verdict › hold — first capture event pending, T+38s`.

### 4.4 Metrics ribbon + timeline
- 4 metrics, tabular 32px: `₹1,997 recovered · 3 retries blocked · 0 duplicates · 0 violations`. Violations metric is permanently green-zero — it's the thesis.
- Event timeline: hairline rows, mono timestamps right-aligned, event name + state pill. New rows flash `--accent-soft` once (240ms) then settle. This is the audit trail made visible.

## 5. First-frame acceptance test (run before shipping any UI slice)

Screenshot the World at 1440×900 and check, without reading body text:

1. Do you know it's a **payments** product in <2 seconds? (phone + money + rails)
2. Do the **three truths** read as three distinct roles?
3. Is there exactly **one** color telling you where the danger is? (amber pending)
4. Does anything look like a default Tailwind/shadcn starter? (fail if yes)
5. Squint test: does the hierarchy still read? (big number → gate → panes)

## 6. Copy tone (product voice)

Short, factual, calm. `Payment captured. Order linked.` not `🎉 Success!!`. Blocked states say *why* and *what instead*. Customer-facing messages in the phone pane read exactly like real UPI app copy — that authenticity is the illusion that sells the whole demo.

## 7. Explicit bans for this UI

No gradient meshes · no glassmorphism · no emoji as decoration · no purple-blue AI-sparkle clichés · no lorem ipsum or "John Doe" (use synthetic-but-real Indian demo data: `Aarav S.`, `FitCart order #1241`) · no default focus-ring removal · no library default blue links · no stock 3D illustrations.

## 8. Build order note for the agent

Tokens → primitives (`Button`, `Pill`, `Metric`, `Pane`, `EventRow`) → panes → World grid → motion pass → first-frame screenshot test. Primitives before pages, always.
