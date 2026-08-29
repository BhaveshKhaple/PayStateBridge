# Evaluation Suite

## Usage

```bash
# Dev split (tuning allowed)
python -m app.evals.runner --split dev

# Heldout split (sealed — do not edit files in data/incidents/heldout/)
python -m app.evals.runner --split heldout

# Full report with JSON output
python -m app.evals.runner --split all --json-out report.json
```

## Metrics

| Metric | Target | Safety gate |
|---|---|---|
| State classification accuracy | 85%+ | No |
| **Unsafe retry-link rate** | **0%** | **Yes — exits 1** |
| Captured-unlinked recall | 80%+ | No |
| Duplicate-success recall | 80%+ | No |
| Evidence-packet completeness | 90%+ | No |

## Dataset

- **Dev split:** `data/incidents/dev/` — 36 incidents (INC-0001 to INC-0036)
- **Heldout split:** `data/incidents/heldout/` — 24 incidents (INC-H001 to INC-H024)
- **Heldout rule:** Never edit expected labels while tuning the classifier.

## Safety law

If ANY incident with expected state `PENDING` or `OUTCOME_UNKNOWN` receives action `CREATE_RECOVERY_PERMIT`, the runner exits with code 1 and CI fails.
