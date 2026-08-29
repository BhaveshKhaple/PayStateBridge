# Slice 5 — Evaluation & Quality

**Phase goal:** 60 labelled synthetic incidents (36 dev + 24 heldout), eval runner with all metrics, Playwright E2E flows, GitHub Actions CI fix.
**Date target:** 04/09/2026
**Tasks:** S5-01, S5-02, S5-03

## Acceptance criteria

- [ ] 60 total incidents: 36 dev + 24 heldout
- [ ] All case types represented including malformed + extractor failures
- [ ] Heldout set in separate folder, never edited during tuning
- [ ] Eval runner produces JSON + Markdown report
- [ ] Unsafe retry-link rate = 0 (exits non-zero if violated)
- [ ] State accuracy, captured-unlinked recall, duplicate recall, evidence-packet completeness all reported
- [ ] Simulated GMV labelled synthetic in output
- [ ] GitHub Actions CI: lint + typecheck + pytest + build all pass
- [ ] package-lock.json committed for npm ci
- [ ] CI runs without real credentials
