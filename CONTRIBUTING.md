# Contributing

This is a Razorpay AI Buildathon solo project. Not accepting contributions during the buildathon period (until 05/09/2026).

## Development rules (for maintainer)

1. `APP_ENV=demo` always. Never commit real credentials.
2. Synthetic data only. No real UTRs, screenshots, or customer data.
3. Run eval safety gate before any push: `python -m app.evals.runner --split dev`
4. All money stored as integer paise.
5. Gateway evidence always outranks customer report.
6. AI may extract fields only — never decide payment state.
