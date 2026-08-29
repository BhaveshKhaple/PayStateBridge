# Local Setup Guide — PayState Bridge

Complete guide to run PayState Bridge locally for development or demo.

## Requirements

| Tool | Version | Check |
|---|---|---|
| Python | 3.12+ | `python --version` |
| Node.js | 22+ LTS | `node --version` |
| Git | any | `git --version` |

## Step-by-step

### 1. Clone

```bash
git clone https://github.com/BhaveshKhaple/PayStateBridge.git
cd PayStateBridge
```

### 2. Environment file

```bash
cp .env.example .env
```

Edit `.env`:
```
APP_ENV=demo                          # required — must be exactly "demo"
DATABASE_URL=sqlite+aiosqlite:///./paystate.db
GEMINI_API_KEY=                       # optional — leave empty to use FakeExtractor
RAZORPAY_KEY_ID=                      # optional — must start with rzp_test_ if set
RAZORPAY_KEY_SECRET=                  # required if KEY_ID is set
RAZORPAY_WEBHOOK_SECRET=              # required for live webhook testing
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Python API

```bash
cd apps/api
python -m venv .venv
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m app.db.seed
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

**macOS / Linux:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

Expected seed output:
```
Seeded 36 synthetic dev incidents into SQLite.
SYNTHETIC DATA ONLY — no real payment data.
```

### 4. Next.js web (new terminal)

```bash
cd apps/web
npm install
npm run dev
```

### 5. Verify

```bash
# Health check
curl http://localhost:8000/health
# → {"status":"healthy","service":"paystate-bridge-api"}

# List cases (after seed)
curl http://localhost:8000/v1/cases
# → [...array of 36 cases...]
```

Open http://localhost:3000/cases — you should see 36 synthetic payment cases.

## Running tests

```bash
cd apps/api

# All tests (no API keys needed)
.venv/Scripts/pytest --tb=short -q   # Windows
pytest --tb=short -q                  # macOS/Linux

# Evaluation safety gate
python -m app.evals.runner --split dev
python -m app.evals.runner --split heldout

# Full report
python -m app.evals.runner --split all --json-out report.json
```

## Using Gemini (optional)

1. Get a Gemini API key from https://aistudio.google.com/
2. Add to `.env`: `GEMINI_API_KEY=your_key_here`
3. Restart the API
4. The extraction endpoint will now use `GeminiEvidenceExtractor` instead of `FakeEvidenceExtractor`

## Using Razorpay Test Mode (optional)

1. Create a Razorpay account at https://razorpay.com/
2. Switch to **Test Mode** in the dashboard
3. Copy `rzp_test_` Key ID and Key Secret
4. Add to `.env`:
   ```
   RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXX
   RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXX
   ```
5. Restart API — live provider will be used instead of FakePaymentProvider

**Note:** Razorpay Test Mode is limited to ~30 Payment Links per business. Use FakeProvider for automated testing.

## Troubleshooting

| Issue | Fix |
|---|---|
| `ConfigError: APP_ENV must be 'demo'` | Set `APP_ENV=demo` in `.env` |
| `ConfigError: RAZORPAY_KEY_ID must start with rzp_test_` | You have a live key — replace with test key |
| Port 8000 in use | `uvicorn app.main:app --reload --port 8001` and update `NEXT_PUBLIC_API_URL` |
| `No JSON files found` during seed | Verify `data/incidents/dev/` has INC-0001.json through INC-0036.json |
| Next.js build fails | Run `npm install` first from `apps/web/` |
