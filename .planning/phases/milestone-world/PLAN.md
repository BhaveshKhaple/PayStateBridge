# Milestone: PayState World — Three-Pane Simulator

**Goal:** Turn the CRUD console into a live simulator where a judge watches three truths diverge (customer / rails / merchant), tries to break the safety law via a Chaos Panel, and watches the real policy engine hold the line.
**Specs:** docs/EXPERIENCE_AND_SIMULATOR.md + docs/UI_DESIGN_SYSTEM.md
**Deadline:** 05/09/2026

## Non-negotiables
- The sim does NOT fake the agent. It emits real PSP-shaped events; the existing classifier/policy engine consumes them. The gate that slams is a REAL policy decision.
- SSE (not WebSocket). Deterministic seeds. Same story replays identically.
- Dark theme only, done excellently. Design tokens from UI_DESIGN_SYSTEM.md §1.
- Color = state globally: amber=PENDING, red=blocked, green=recovered, grey=unknown.
- Money/IDs always mono + tabular-nums.

## Slices

| Slice | Task | Proves |
|---|---|---|
| X-00 | Design tokens (globals.css) + primitives (Button, Pill, Metric, Pane, EventRow) | Foundation, no Tailwind-starter look |
| X-01 | Sim engine (deterministic scheduler) + SSE stream + 1 fixture | World ticks, events flow |
| X-02 | PhonePane — pay → processing → debited → pay-again temptation | Customer truth visible |
| X-03 | RailsPane (SVG nodes + moving packet) + Chaos Panel | God view + judge injects failure |
| X-04 | ConsolePane gate + TruthBar + Metrics ribbon | The BLOCKED moment lands |
| X-05 | 3 Judge Mode stories + timeline scrubber | The demo script |
| X-06 | Vercel/Railway deploy + record 3 stories | Live URL (needs user accounts — manual) |

## Acceptance
- [ ] World view at /world, 100dvh, three panes 1fr/1.2fr/1fr, hairline dividers
- [ ] SSE stream drives all three panes from one deterministic event log
- [ ] Chaos Panel: webhook delay slider, lose webhook, mash pay again, bank timeout, double-click race
- [ ] Gate slam: pressing "pay again" while PENDING → red shake + evidence chain
- [ ] Metrics ribbon: ₹ recovered · retries blocked · duplicates prevented · violations 0
- [ ] 3 stories one-click replay; timeline scrubber drags through event window
- [ ] First-frame test passes (payments product in <2s, 3 truths, one danger color)
